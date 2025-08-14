import unittest
import email_content

class TestMarkdownToHtml(unittest.TestCase):

    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        self.maxDiff = None  # To see full diff in case of failure

    def test_markdown_to_html(self):
        with open('tests/sample.md', 'r', encoding='utf-8') as f:
            md_text = f.read()
        html_actual = email_content.markdown_to_html(md_text)
        # print(html_actual)  # For debugging purposes
        with open('tests/sample.html', 'r', encoding='utf-8') as f:
            html_expected = f.read()
        self.assertEqual(html_actual.strip(), html_expected.strip())

if __name__ == "__main__":
    unittest.main()
