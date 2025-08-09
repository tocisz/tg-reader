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

        class MarkdownPreprocessor(markdown.preprocessors.Preprocessor):
            """
            Preprocess markdown to ensure bullet points are recognized by markdown parser.
            Implements the markdown Preprocessor API: run(lines) -> list[str]
            """
            def run(self, lines):
                new_lines = []
                prev_blank = True
                for line in lines:
                    stripped = line.lstrip()
                    if (stripped.startswith('* ') or stripped.startswith('- ') or stripped.startswith('+ ')):
                        if not prev_blank:
                            new_lines.append('')
                        new_lines.append(line)
                        prev_blank = False
                    else:
                        new_lines.append(line)
                        prev_blank = (stripped == '')
                return new_lines

        class PreExt(markdown.extensions.Extension):
            def extendMarkdown(self, md):
                md.preprocessors.register(MarkdownPreprocessor(md), 'fix_bullets', 27)

        return markdown.markdown(md_text, extensions=[PreExt()])

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
