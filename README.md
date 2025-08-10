# Telegram Group Reader & Summarizer

This script fetches messages from a specified Telegram group, organizes them into threads, and can generate an AI summary using Google's Gemini model. It saves both the raw thread output and the summary to files in the `chats` subdirectory.

## Features
- Fetches messages from a Telegram group (by name)
- Groups messages into threads based on replies
- Caches usernames and group info for efficiency
- Saves thread output as a `.txt` file
- Optionally summarizes the discussion using Gemini AI and saves as a `.md` file
- All outputs are saved in the `chats` directory

## Configuration (`config.json`)
Create a `config.json` file in the same directory as the script with the following structure:

```
{
  "api_id": <your_telegram_api_id>,
  "api_hash": "<your_telegram_api_hash>",
  "gemini_api_key": "<your_google_gemini_api_key>",
  "gemini_model": "gemini-2.5-flash", // or another Gemini model name
  "gemini_prompt": "Summarize the following Telegram group discussion:" // (optional, customizes summary prompt)
}
```
- `api_id` and `api_hash` are required for Telegram API access. Get them from https://my.telegram.org.
- `gemini_api_key` is required for AI summarization. Get it from Google AI Studio.
- `gemini_model` is the Gemini model name (default: `gemini-2.5-flash`).
- `gemini_prompt` (optional) customizes the prompt for the AI summary.

## Installation

### 1. Create a virtual environment (recommended)

```
python3 -m venv .venv
```

### 2. Activate the virtual environment and install dependencies

```
source .venv/bin/activate
pip install -r install.txt
```

## Usage


You can run the script using the provided shell wrapper (recommended):

```
./tg <group_name> [--cutoff YYYY-MM-DD] [--limit N] [--summarize]
```

Or directly with Python:

```
.venv/bin/python tg.py <group_name> [--cutoff YYYY-MM-DD] [--limit N] [--summarize]
```

- `<group_name>`: Name of the Telegram group (as shown in your dialogs). If omitted, lists available groups.
- `--cutoff`: Only fetch messages after this date/time (ISO format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`).
- `--limit`: Maximum number of messages to fetch (default: 100).
- `--summarize`: Generate an AI summary using Gemini and save as Markdown.

### Example

```
python tg.py "My Group" --cutoff 2025-08-01 --limit 200 --summarize
```

This will fetch up to 200 messages from "My Group" since August 1, 2025, print and save the threads, and generate a Gemini summary in Markdown.

## Output
- Thread output: `chats/<group_name>_<lastmsgdate>.txt`
- Gemini summary: `chats/<group_name>_<lastmsgdate>.md`

## Notes
- The script caches usernames and group info for efficiency.
- If you run without a group name, it will list all available groups.
- The Gemini summary requires a valid API key and model.

## AWS Lambda Deployment

You can deploy the summarizer to AWS Lambda for scheduled, serverless operation. See [`AWS.md`](./AWS.md) for a full step-by-step deployment guide, including configuration, SES setup, and troubleshooting.

**Important:**
- You must first run the summarizer locally to generate the `telegram.session` file, then upload it to your S3 bucket as described in `AWS.md`.
- The deployment script (`deploy_aws.sh`) automates most AWS setup, but you must confirm SES email verification and upload your session file manually.

For advanced configuration, scheduling, and troubleshooting, refer to [`AWS.md`](./AWS.md).

---

MIT License
