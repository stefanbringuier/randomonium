import requests
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
from markdown.treeprocessors import Treeprocessor

from markdown.inlinepatterns import InlineProcessor
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

import html
import re
import sys
import os
import base64
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from bs4 import BeautifulSoup

import emoji

class LinkPreviewPostprocessor(Postprocessor):
    def run(self, text):
        soup = BeautifulSoup(text, 'html.parser')

        # Extract references and footnotes text
        references_text = self.extract_section_text(soup, 'References')
        footnotes_text = self.extract_footnotes_text(soup)

        # Add 'data-preview' attribute to internal links to references and footnotes
        for a in soup.find_all('a', href=True):
            if '#References' in a['href']:
                a['data-preview'] = references_text
            elif a['href'].startswith('#fn:'):
                footnote_key = a['href'].lstrip('#')
                a['data-preview'] = footnotes_text.get(footnote_key, '')

            a['class'] = a.get('class', []) + ['preview-link']

        return str(soup)

    @staticmethod
    def extract_section_text(soup, section_id):
        section = soup.find('h4', string=lambda text: text and text.lower() == section_id.lower())
        if not section:
            return ''

        # Accumulate text from all sibling elements after the section header
        text = []
        for sibling in section.find_next_siblings():
            text.append(' '.join(sibling.stripped_strings))
            if sibling.name and sibling.name.startswith('h'):
                break  # Stop if another header is reached
        return ' '.join(text)

    @staticmethod
    def extract_footnotes_text(soup):
        footnotes = {}
        for footnote in soup.find_all('div', class_='footnote'):
            footnote_id = footnote.get('id', '')
            footnotes[footnote_id] = ' '.join(footnote.stripped_strings)
        return footnotes
    
class LinkPreviewExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(LinkPreviewPostprocessor(md), "link_preview", 175)

class CustomCSSPostprocessor(Postprocessor):
    def run(self, text):
        custom_css = """
<style>
.custom-table {
    border-collapse: collapse;
    font-size: 10.5px; 
    width: 100%;
}
.custom-table th, .custom-table td {
    padding: 1px;
    text-align: left;
}
.custom-table th {
    background-color: #d3d3d3;
    color: #000;
    border-bottom: 1px solid #000; 
    border-top: 1.5px solid #000; 
}
.custom-table tr:first-child td{
    border-top: 1.0px solid #000;
}
.custom-table tr:last-child td {
    border-bottom: 1.5px solid #000; 
}
.inline-code-highlight {
    background-color: #f9f2f4;
    color: #c7254e;
    padding: 2px 4px;
    font-size: 90%;
    border-radius: 4px;
}
</style>
"""
        return custom_css + text  # Insert the custom CSS at the beginning of the HTML

class TableClassPostprocessor(Postprocessor):
    def run(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        for table in soup.find_all('table'):
            table['class'] = table.get('class', []) + ['custom-table']
        return str(soup)
    
class CustomCSSExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(CustomCSSPostprocessor(md), 'custom_css', 5)


class TableClassExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(TableClassPostprocessor(md), 'table_class', 5)

# Updated CodeBlockPreprocessor
class CodeBlockPreprocessor(Preprocessor):
    CODE_BLOCK_RE = re.compile(r'^```(\w+)?\s*$')
    END_CODE_BLOCK_RE = re.compile(r'^```\s*$')

    def __init__(self, md, **options):
        super().__init__(md)
        self.formatter = HtmlFormatter(nowrap=False, **options)

    def run(self, lines):
        new_lines = []
        code_block = []
        in_code_block = False
        lang = 'text'

        for line in lines:
            if in_code_block:
                if self.END_CODE_BLOCK_RE.match(line):
                    code = '\n'.join(code_block)
                    highlighted_code = self._highlight_code(lang, code)
                    new_lines.append(highlighted_code)
                    code_block = []
                    in_code_block = False
                else:
                    code_block.append(line)
            else:
                match = self.CODE_BLOCK_RE.match(line)
                if match:
                    in_code_block = True
                    lang = match.group(1) or 'text'
                else:
                    new_lines.append(line)
        # If code block wasn't closed
        if code_block:
            code = '\n'.join(code_block)
            highlighted_code = self._highlight_code(lang, code)
            new_lines.append(highlighted_code)
        return new_lines

    def _highlight_code(self, lang, code):
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            lexer = TextLexer()
        self.formatter = HtmlFormatter(nowrap=True)  # Ensures no extra <pre> tags
        highlighted = highlight(code, lexer, self.formatter)
        return f'<pre class="language-{lang}"><code>{highlighted}</code></pre>'

# Updated InlineCodePreprocessor
class InlineCodePreprocessor(Preprocessor):
    INLINE_CODE_RE = re.compile(r"`(?P<code>.+?)`", re.DOTALL)

    def __init__(self, md):
        super().__init__(md)
        self.formatter = HtmlFormatter(nowrap=True)

    def run(self, lines):
        def repl(m):
            code = m.group("code").replace("\n", " ")
            lexer = TextLexer()
            highlighted_code = highlight(code, lexer, self.formatter)
            highlighted_code = highlighted_code.rstrip()  # Remove trailing spaces
            return '<span class="inline-code-highlight">%s</span>' % highlighted_code

        text = "\n".join(lines)
        text = self.INLINE_CODE_RE.sub(repl, text)
        return text.split("\n")

class CodeBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CodeBlockPreprocessor(md), "code_block", 175)
        md.preprocessors.register(InlineCodePreprocessor(md), "inline_code", 150)

class ImagePreprocessor(Preprocessor):
    IMAGE_RE = re.compile(r"!\[(.*?)\]\((.*?)\)")

    def __init__(self, md, markdown_file_dir):
        super().__init__(md)
        self.markdown_file_dir = markdown_file_dir

    def run(self, lines):
        def repl(m):
            alt_text = m.group(1)
            image_path = m.group(2)
            image_data = None
            image_ext = None

            if image_path.startswith(("http://", "https://", "www")):
                response = requests.get(image_path)
                image_data = response.content
                image_ext = os.path.splitext(image_path)[1][1:]  # Extension from URL
            else:
                # Resolve relative path for local files
                full_image_path = os.path.join(self.markdown_file_dir, image_path)
                if os.path.exists(full_image_path):
                    with open(full_image_path, "rb") as image_file:
                        image_data = image_file.read()
                    image_ext = os.path.splitext(full_image_path)[1][1:]  # Extension from local file
                else:
                    return m.group()  # Return original markdown if file not found

            # Encode the image data
            encoded_string = base64.b64encode(image_data).decode()
            data_url = f"data:image/{image_ext};base64,{encoded_string}"

            table = etree.Element(
                "table",
                attrib={
                    "align": "center",
                    "cellpadding": "0",
                    "cellspacing": "0",
                    "class": "tr-caption-container",
                    "style": "margin-left: auto; margin-right: auto;",
                },
            )
            tbody = etree.SubElement(table, "tbody")
            tr1 = etree.SubElement(tbody, "tr")
            td1 = etree.SubElement(tr1, "td", attrib={"style": "text-align: center;"})
            img = etree.SubElement(
                td1, "img", attrib={"border": "0", "src": data_url, "width": "500"}
            )
            tr2 = etree.SubElement(tbody, "tr")
            td2 = etree.SubElement(
                tr2,
                "td",
                attrib={"class": "tr-caption", "style": "text-align: center;"},
            )
            soup = BeautifulSoup(markdown.markdown(alt_text), features="html.parser")
            td2.text = ''.join(soup.stripped_strings)  # Extracts all text from the rendered Markdown, discarding the tags
            
            # Convert the element to a string and return
            return etree.tostring(table, encoding="unicode")

        new_lines = []
        for line in lines:
            new_line = self.IMAGE_RE.sub(repl, line)
            new_lines.append(new_line)

        return new_lines

class ImageExtension(Extension):
    def __init__(self, markdown_file_dir):
        self.markdown_file_dir = markdown_file_dir

    def extendMarkdown(self, md):
        image_preprocessor = ImagePreprocessor(md, self.markdown_file_dir)
        md.preprocessors.register(image_preprocessor, "image_preprocessor", 125)
        md.preprocessors.deregister("html_block")

class LatexPreprocessor(Preprocessor):
    def __init__(self, md):
        super().__init__(md)

    def process_latex_content(self, text):
        # Replacing specific LaTeX commands using regular expressions
        replacements = {
            r'\\\\': r'\\\\\\\\',
            '_': r'\_',  # Escaping Markdown underscore
            '\*': r'\*',  # Escaping Markdown asterisk
        }

        for old, new in replacements.items():
            text = re.sub(old, new, text)
        return text

    def run(self, lines):
        # Concatenate lines into a single string
        text = "\n".join(lines)
        latex_pattern = re.compile(
            r"(\$\$.*?\$\$|\$.*?\$)",
            flags=re.DOTALL
        )

        # Apply replacements to the entire text
        text = latex_pattern.sub(lambda m: self.process_latex_content(m.group(0)), text)

        # Split back into lines
        return text.split("\n")

class LatexExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(LatexPreprocessor(md), "latex_escape", 175)

class MetaDataPreprocessor(Preprocessor):
    META_PATTERN = re.compile(r"<!-- META: (.+?) -->")

    def __init__(self, md):
        super().__init__(md)

    def run(self, lines):
        metadata = {}
        meta_lines = []

        for line in lines:
            match = self.META_PATTERN.match(line)
            if match:
                meta_data = match.group(1)
                # Parse the metadata and extract relevant information
                # For example, split by commas to extract tags
                key_values = [item.strip() for item in meta_data.split(",")]
                for key_value in key_values:
                    key, value = key_value.split("=")
                    metadata[key.strip()] = value.strip()
                meta_lines.append(line)
            else:
                break  # Stop processing when encountering non-meta line

        # Store the metadata in some way (e.g., in a global variable, database, etc.)
        print("Metadata:", metadata)

        # Return the remaining lines for further Markdown processing
        return lines[len(meta_lines):]

class MetaDataExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MetaDataPreprocessor(md), "meta_data", 0)

class RawLinkPreprocessor(Preprocessor):
    # Matches both URLs within markdown links and standalone URLs
    URL_RE = re.compile(r"(\[([^]]+)\]\((https?://[^\s]+)\))|(https?://[^\s]+)")

    def __init__(self, md):
        super().__init__(md)

    def run(self, lines):
        def repl(m):
            # If the URL is part of a markdown link, leave it as is
            if m.group(2) is not None and m.group(3) is not None:
                return m.group(1)
            # Otherwise, turn it into an HTML link
            else:
                url = m.group(4)
                return f'<a href="{url}">{url}</a>'

        new_lines = []
        for line in lines:
            new_line = self.URL_RE.sub(repl, line)
            new_lines.append(new_line)

        return new_lines

class RawLinkExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(RawLinkPreprocessor(md), "raw_link", 100)

class EmojiPreprocessor(Preprocessor):
    def __init__(self, md):
        super().__init__(md)

    def run(self, lines):
        new_lines = []
        for line in lines:
            line = emoji.emojize(line)  # Convert text-based emojis
            #line = emoji.demojize(line)
            new_lines.append(line)
        return new_lines

class EmojiExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(EmojiPreprocessor(md), "emoji_preprocessor", 175)

class ReferencesIdTreeprocessor(Treeprocessor):
    def run(self, root):
        for element in root.iter():
            if element.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if element.text and "references" in element.text.lower():
                    element.set("id", "references")
        return root

class ReferencesIdExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(ReferencesIdTreeprocessor(md), "references_id", 50)

class StylingPostprocessor(Postprocessor):
    def run(self, text):
        text = self.format_text(text)
        return text

    def format_text(self, text):
        # Split the document into three parts at the "References" and "Footnotes" heading
        parts = re.split(r"(?si)(<h[1-6] id=\"references\">.*?</h[1-6]>|<h[1-6]>Footnotes.*?</h[1-6]>)", text)
        
        # Apply text replacements to each part separately
        # The text before References
        parts[0] = re.sub(r"<p>", r'<p style="text-align: justify;">', parts[0])

        if len(parts) >= 3:
            # The text between References and Footnotes
            parts[2] = re.sub(r"<p>", r'<p style="text-align: left; font-size: 12px;">', parts[2])

        # The text after Footnotes
        if len(parts) == 5:
            parts[4] = re.sub(r"<p>", r'<p style="text-align: left; font-size: 12px;">', parts[4])

        return "".join(parts)

class StylingExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(StylingPostprocessor(md), "styling", 175)

class IncludeHTMLPostprocessor(Postprocessor):
    def run(self, text):
        def replace_include(match):
            filename = match.group(1)
            try:
                with open(filename, 'r') as f:
                    html_content = f.read()
                return html_content
            except FileNotFoundError:
                # If the file is not found, return the original placeholder or handle it appropriately
                return match.group(0)
        
        # Use re.sub to find the pattern and replace it by reading the file content
        new_text = re.sub(r'\{\{\s*include\s+(.*?)\s*\}\}', replace_include, text)
        return new_text

class IncludeHTMLExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(IncludeHTMLPostprocessor(md), 'include_html', 25)

def process(infile):
    markdown_file_dir = os.path.dirname(os.path.abspath(infile))

    with open(infile, "r") as f:
        text = f.read()
    html = markdown.markdown(
        text,
        extensions=[
            CodeBlockExtension(),
            LatexExtension(),
            "fenced_code",
            "tables",
            "footnotes",
            "admonition",
            ImageExtension(markdown_file_dir),
            MetaDataExtension(),
            ReferencesIdExtension(),
            StylingExtension(),
            EmojiExtension(),
            LinkPreviewExtension(),
            IncludeHTMLExtension(),
            CustomCSSExtension(),
            TableClassExtension()
        ],
        extension_configs={"footnotes": {"PLACE_MARKER" : "///Footnotes///"}},
    )
    return html

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    html = process(infile)
    with open(outfile, "w") as f:
        f.write(html)
