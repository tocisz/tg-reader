#!/usr/bin/env python3

import json
import os
import argparse

from telethon import TelegramClient
from datetime import datetime
from datetime import timezone
from collections import defaultdict
import google.generativeai as genai
from typing import Any, Optional


# These example values won't work. You must get your own api_id and
# api_hash from https://my.telegram.org, under API Development.
with open('config.json', 'r') as f:
    config = json.load(f)
api_id = config['api_id']
api_hash = config['api_hash']


# Gemini config (optional)
GEMINI_API_KEY = config.get('gemini_api_key')
GEMINI_MODEL = config.get('gemini_model', 'gemini-2.5-flash')
GEMINI_PROMPT = config.get('gemini_prompt', 'Summarize the following Telegram group discussion:')


USER_CACHE_FILE = "user_cache.json"
GROUP_INFO_FILE = "group_info.json"
def load_group_info() -> dict:
    if not os.path.exists(GROUP_INFO_FILE):
        return {}
    with open(GROUP_INFO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_group_info(info: dict) -> None:
    with open(GROUP_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

def load_user_cache() -> dict:
    """Load sender ID → username mapping."""
    if not os.path.exists(USER_CACHE_FILE):
        return {}
    with open(USER_CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_cache(cache: dict) -> None:
    """Save sender ID → username mapping."""
    with open(USER_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

async def get_username(sender: str) -> str:
    """Get a display name for the sender."""
    if sender.username:
        return f"@{sender.username}"
    return f"{sender.first_name or ''} {sender.last_name or ''}".strip()

client = TelegramClient('telegram', api_id, api_hash)

def gemini_summarize(thread_output: str) -> str:
    """Summarize the thread output using Gemini API via google-genai."""
    prompt = GEMINI_PROMPT + "\n\n" + thread_output
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Gemini API error: {e}]"


async def list_groups_async(client: str) -> None:
    group_map = await get_group_map(client)
    if group_map:
        print("Available groups:")
        for name, chat_id in group_map.items():
            print(f"- {name}: {chat_id}")
    else:
        print("No groups found.")

# Synchronous entrypoint for listing groups
def list_groups() -> None:
    with client:
        client.loop.run_until_complete(list_groups_async(client))

async def get_group_map(client: Any) -> dict:
    group_map = {}
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group_map[dialog.name] = dialog.id
    return group_map


async def main_async(
    client: Any, group_name: str, cutoff_time: Optional[str] = None, message_limit: int = 1000, summarize: bool = False, silent: bool = False
) -> list[str]:
    group_map = await get_group_map(client)
    user_cache = load_user_cache()
    group_info = load_group_info()

    # Special handling for group_name == 'all'
    if group_name == 'all':
        created_files = []
        for name in group_map:
            if name.lower() == 'all':
                continue
            print(f"\n=== Processing group: {name} ===")
            files = await main_async(client, name, cutoff_time, message_limit, summarize, silent)
            if files:
                created_files.extend(files)
        return created_files

    if not group_name:
        print("Group name is required.")
        return []

    group_id = group_map.get(group_name)
    if not group_id:
        print(f"Group '{group_name}' not found. Available groups:")
        for name in group_map:
            print(f"- {name}")
        return []

    print(f"Fetching messages from group: {group_id}")

    messages = []

    # Use last message date from group_info as default cutoff if not provided
    last_date_str = group_info.get(group_name, {}).get("last_message_date")
    if not cutoff_time and last_date_str:
        cutoff_time = last_date_str

    if cutoff_time:
        try:
            cutoff_dt = datetime.fromisoformat(cutoff_time)
            # If cutoff_dt is naive, make it UTC-aware
            if cutoff_dt.tzinfo is None:
                cutoff_dt = cutoff_dt.replace(tzinfo=timezone.utc)
        except Exception:
            print("Invalid cutoff time format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")
            return

    last_message_date = None
    created_md_files = []
    idx = 0
    async for message in client.iter_messages(group_id, limit=message_limit):
        # Compare with date from group_info.json
        if idx == 0:
            if cutoff_dt and message.date == cutoff_dt:
                print(f"No new messages in group '{group_name}'. Skipping.")
                return
        idx += 1

        if cutoff_dt and message.date < cutoff_dt:
            break

        sender_id = message.sender_id
        timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")

        if sender_id is None:
            name = "Unknown"
        elif str(sender_id) in user_cache:
            name = user_cache[str(sender_id)]
        else:
            sender = await message.get_sender()
            name = await get_username(sender) if sender else "Unknown"
            user_cache[str(sender_id)] = name

        messages.append({
            'id': message.id,
            'sender_id': sender_id,
            'name': name,
            'text': message.text,
            'timestamp': timestamp,
            'reply_to': message.reply_to.reply_to_msg_id if message.reply_to else None
        })

        # Track the latest message date
        if last_message_date is None or message.date > last_message_date:
            last_message_date = message.date

    # Group into threads
    threads = defaultdict(list)
    for msg in reversed(messages):
        if msg['reply_to']:
            threads[msg['reply_to']].append(msg)
        else:
            threads[msg['id']].append(msg)

    # Prepare thread output as string
    thread_lines = []
    for root_id, msgs in threads.items():
        if len(msgs) > 1:
            thread_lines.append("\n<thread>")
        for m in msgs:
            thread_lines.append(f"[{m['timestamp']}] {m['name']}: {m['text']}")
        if len(msgs) > 1:
            thread_lines.append("</thread>\n")

    thread_output = "\n".join(thread_lines)
    if not silent:
       print(thread_output)

    # Save thread output to file in chats subdirectory
    if last_message_date:
        safe_group = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in group_name)
        date_str = last_message_date.strftime("%Y%m%d_%H%M%S")
        out_dir = "chats"
        os.makedirs(out_dir, exist_ok=True)
        out_filename = os.path.join(out_dir, f"{safe_group}_{date_str}.txt")
        with open(out_filename, "w", encoding="utf-8") as f:
            f.write(thread_output)
        summary_filename = os.path.join(out_dir, f"{safe_group}_{date_str}.md")

    # Summarize with Gemini if requested
    if summarize:
        if not GEMINI_API_KEY or not GEMINI_MODEL:
            print("Gemini API key or model not set in config.json. Skipping summarization.")
        else:
            print("\nSummarizing with LLM...")
            summary = gemini_summarize(thread_output)
            if not silent:
                print("\nSummary:\n")
                print(summary)
            # Save summary to markdown file in chats subdirectory
            if last_message_date:
                with open(summary_filename, "w", encoding="utf-8") as f:
                    f.write(f"# Summary for {group_name} ({date_str})\n\n")
                    f.write(summary)
                created_md_files.append(summary_filename)

    # Save user cache and group info at the end
    save_user_cache(user_cache)

    # Update group_info with last message date
    if last_message_date:
        if group_name not in group_info:
            group_info[group_name] = {}
        group_info[group_name]["last_message_date"] = last_message_date.isoformat()
        save_group_info(group_info)

    return created_md_files

# Synchronous entrypoint for CLI usage
def main(
    group_name: str, cutoff_time: Optional[str] = None, message_limit: int = 1000, summarize: bool = False, silent: bool = False
) -> list[str]:
    with client:
        return client.loop.run_until_complete(
            main_async(client, group_name, cutoff_time, message_limit, summarize, silent)
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram group message fetcher")
    parser.add_argument("group_name", nargs="?", default=None, help="Name of the Telegram group (if omitted, lists groups)")
    parser.add_argument("--cutoff", dest="cutoff_time", default=None, help="Cutoff time (ISO format, e.g. 2024-01-01 or 2024-01-01T12:00:00)")
    parser.add_argument("--limit", dest="message_limit", type=int, default=1000, help="Message limit (default 1000)")
    parser.add_argument("--summarize", action="store_true", help="Summarize messages using Gemini model from Google")
    parser.add_argument("--silent", action="store_true", help="Suppress output to standard output")
    args = parser.parse_args()

    if not args.group_name:
        list_groups()
    else:
        main(args.group_name, args.cutoff_time, args.message_limit, args.summarize, args.silent)