import os
from typing import List, Tuple
from multipart import EmailMessageData, EmailAttachment

def extract_title_and_body(md_path: str) -> Tuple[str, str]:
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


def markdown_to_html(md_text: str) -> str:
    try:
        import markdown

        class FixBulletsAndEnumerations(markdown.preprocessors.Preprocessor):
            """
            Preprocess markdown to ensure bullet points are recognized by markdown parser.
            Implements the markdown Preprocessor API: run(lines) -> list[str]
            """
            def run(self, lines):
                new_lines = []
                prev_blank = True
                for line in lines:
                    stripped = line.lstrip()
                    # Detect bullet points (unordered)
                    is_bullet = (
                        stripped.startswith('* ') or stripped.startswith('- ') or stripped.startswith('+ ')
                    )
                    # Detect enumerated list (ordered)
                    is_enum = False
                    if len(stripped) > 2 and stripped[0].isdigit():
                        # e.g. 1. or 2. or 10.
                        dot_idx = stripped.find('.')
                        if dot_idx > 0 and stripped[:dot_idx].isdigit() and stripped[dot_idx+1:dot_idx+2] == ' ':
                            is_enum = True

                    if is_bullet or is_enum:
                        if not prev_blank:
                            new_lines.append('')
                        new_lines.append(line)
                        prev_blank = False
                    else:
                        new_lines.append(line)
                        prev_blank = (stripped == '')
                return new_lines

        class AddPreprocessors(markdown.extensions.Extension):
            def extendMarkdown(self, md):
                md.preprocessors.register(FixBulletsAndEnumerations(md), 'fix_bullets', 27)

        return markdown.markdown(md_text, extensions=[AddPreprocessors()])

    except ImportError:
        # Fallback: wrap in <pre>
        return f"<pre>{md_text}</pre>"


def generate_emails_from_files(md_files: List[str]) -> List[EmailMessageData]:
    emails = []
    for md_path in md_files:
        title, md_body = extract_title_and_body(md_path)
        html_body = markdown_to_html(md_body)
        txt_path = md_path[:-3] + ".txt" if md_path.endswith('.md') else md_path + ".txt"
        attachments = [EmailAttachment(txt_path, mime_type="text/plain", filename=os.path.basename(txt_path))]
        msg_data = EmailMessageData(
            subject=title,
            sender="",  # Fill in when sending
            recipient="",  # Fill in when sending
            text=md_body,
            html=html_body,
            attachments=attachments
        )
        emails.append(msg_data)
    return emails
