import glob
import os

def get_markdown_files(chats_dir="chats"):
    return sorted(glob.glob(os.path.join(chats_dir, "*.md")))


def extract_title_and_body(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    title = "Telegram Group Summary"
    body_lines = []
    for line in lines:
        if line.strip().startswith("# "):
            title = line.strip().lstrip("# ").strip()
        else:
            body_lines.append(line)
    body = "".join(body_lines)
    return title, body


def markdown_to_html(md_text):
    try:
        import markdown
        return markdown.markdown(md_text)
    except ImportError:
        # Fallback: wrap in <pre>
        return f"<pre>{md_text}</pre>"


def generate_emails_from_chats(chats_dir="chats"):
    md_files = get_markdown_files(chats_dir)
    emails = []
    for md_path in md_files:
        title, md_body = extract_title_and_body(md_path)
        html_body = markdown_to_html(md_body)
        emails.append({
            "title": title,
            "html": html_body,
            "file": md_path
        })
    return emails
