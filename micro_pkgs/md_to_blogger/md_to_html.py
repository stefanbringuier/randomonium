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


import re
import sys
import os
import base64
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter, RawTokenFormatter
from urllib.parse import urlparse

from bs4 import BeautifulSoup


class CodeBlockPreprocessor(Preprocessor):
    CODE_BLOCK_RE = re.compile(r"```(?P<language>\w+)?\n(?P<code>.+?)```", re.DOTALL)

    def run(self, lines):
        def repl(m):
            language = m.group("language")
            if language is None:
                language = "text"
            code = m.group("code")
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(nowrap=True)
            code = highlight(code, lexer, formatter)
            return '\n\n<pre class="language-%s"><code>%s</code></pre>\n\n' % (
                language,
                code,
            )

        text = "\n".join(lines)
        text = self.CODE_BLOCK_RE.sub(repl, text)
        return text.split("\n")


class InlineCodePreprocessor(Preprocessor):
    INLINE_CODE_RE = re.compile(r"`(?P<code>.+?)`", re.DOTALL)

    def run(self, lines):
        def repl(m):
            code = m.group("code").replace("\n", " ")
            lexer = TextLexer()
            formatter = HtmlFormatter(nowrap=True)
            highlighted_code = highlight(code, lexer, formatter)
            highlighted_code = highlighted_code.rstrip()  # Remove trailing spaces
            return '<span class="inline-code-highlight">%s</span>' % highlighted_code

        text = "\n".join(lines)
        text = self.INLINE_CODE_RE.sub(repl, text)
        return text.split("\n")


class CodeBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CodeBlockPreprocessor(md), "code_block", 175)
        md.preprocessors.register(InlineCodePreprocessor(md), "inline_code", 150)

    # md.preprocessors.register(ImagePreprocessor(md), 'image_preprocessor', 125)


# Keep for now. Just does encoding.
""" class ImagePreprocessor(Preprocessor):
    IMAGE_RE = re.compile(r'!\[(.*?)\]\((.*?)\)')

    def run(self, lines):
        def repl(m):
            alt_text = m.group(1)
            image_path = m.group(2)

            # Check if image_path is a URL
            if re.match(r'https?://', image_path):
                response = requests.get(image_path)
                image_data = response.content
                image_ext = os.path.splitext(image_path)[1][1:]  # image extension from URL
            else:
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                image_ext = os.path.splitext(image_path)[1][1:]  # image extension from local file

            encoded_string = base64.b64encode(image_data).decode()

            # Prepare the data URL
            data_url = "data:image/{};base64,{}".format(image_ext, encoded_string)

            return f'![{alt_text}]({data_url})'

        new_lines = []
        for line in lines:
            new_line = self.IMAGE_RE.sub(repl, line)
            new_lines.append(new_line)

        return new_lines 

class ImageExtension(Extension):
    def extendMarkdown(self, md):
       md.preprocessors.register(ImagePreprocessor(md), 'image_preprocessor', 125)
"""


class ImagePreprocessor(Preprocessor):
    """
    Provides image preprocessing.
    1. Uses base64 encoding to put image in HTML.
    2. Structure image in bloggerl like environment.
    """

    IMAGE_RE = re.compile(r"!\[(.*?)\]\((.*?)\)")

    def run(self, lines):
        def repl(m):
            alt_text = m.group(1)
            image_path = m.group(2)

            if image_path.startswith(("http://", "https://", "www")):
                response = requests.get(image_path)
                image_data = response.content
                image_ext = os.path.splitext(image_path)[1][
                    1:
                ]  # image extension from URL
            else:
                try:
                    with open(image_path, "rb") as image_file:
                        image_data = image_file.read()
                    image_ext = os.path.splitext(image_path)[1][
                        1:
                    ]  # image extension from local file
                except FileNotFoundError:
                    return (
                        m.group()
                    )  # If the file isn't found, return the original match

            encoded_string = base64.b64encode(image_data).decode()
            data_url = "data:image/{};base64,{}".format(image_ext, encoded_string)

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
            # td2.text = alt_text
            #td2.text = markdown.markdown(alt_text)  # Render the alt text as Markdown
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
    def extendMarkdown(self, md):
        image_preprocessor = ImagePreprocessor(md)
        md.preprocessors.register(image_preprocessor, "image_preprocessor", 125)
        md.preprocessors.deregister("html_block")


class MetaDataPreprocessor(Preprocessor):
    META_PATTERN = re.compile(r"<!-- META: (.+?) -->")

    def run(self, lines):
        metadata = {}

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
            else:
                break  # Stop processing when encountering non-meta line

        # Store the metadata in some way (e.g., in a global variable, database, etc.)
        print("Metadata:", metadata)

        # Return the remaining lines for further Markdown processing
        return lines[len(metadata) + 1 :]


class MetaDataExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MetaDataPreprocessor(md), "meta_data", 0)


class RawLinkPreprocessor(Preprocessor):
    # Matches both URLs within markdown links and standalone URLs
    URL_RE = re.compile(r"(\[([^]]+)\]\((https?://[^\s]+)\))|(https?://[^\s]+)")

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


# Old Interlink for references
"""
class ReferencesIdPreprocessor(Preprocessor):
   def run(self, lines):
       new_lines = []
       for line in lines:
           if line.lower().startswith("#### references"):
               line += " id=\"references\""
           new_lines.append(line)
       return new_lines


class ReferencesIdExtension(Extension):
   def extendMarkdown(self, md):
       md.preprocessors.register(ReferencesIdPreprocessor(md), "references_id", 50)
"""

class ReferencesIdTreeprocessor(Treeprocessor):
    def run(self, root):
        for element in root.iter():
            if element.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                if "references" in element.text.lower():
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
        if len(parts) >= 3:
            # The text before References
            parts[0] = re.sub(r"<p>", r'<p style="text-align: justify;">', parts[0])

            # The text between References and Footnotes
            parts[2] = re.sub(r"<p>", r'<p style="text-align: left; font-size: 12px;">', parts[2])

            # The text after Footnotes
            if len(parts) == 5:
                parts[4] = re.sub(r"<p>", r'<p style="text-align: left; font-size: 12px;">', parts[4])

        return "".join(parts)



# Old sytling post processor    
""" class StylingPostprocessor(Postprocessor):
    def run(self, text):
        text = self.format_text(text)
        return text

    def format_text(self, text):
        # Split the document into two parts at the "References" heading
        parts = re.split(r"(?s)(<h[1-6]>References.*?</h[1-6]>)", text)

        # Apply text replacements to each part separately
        if len(parts) == 3:
            parts[0] = re.sub(r"<p>", r'<p style="text-align: justify;">', parts[0])
            parts[2] = re.sub(
                r"<p>", r'<p style="text-align: left; font-size: 12px;">', parts[2]
            )

        return "".join(parts)

 """
class StylingExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(StylingPostprocessor(md), "styling", 175)


class StylingExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(StylingPostprocessor(md), "styling", 175)


def process(infile):
    with open(infile, "r") as f:
        text = f.read()
    html = markdown.markdown(
        text,
        extensions=["fenced_code",
            "tables",
            "footnotes",
            "admonition",
            CodeBlockExtension(),
#            InlineCodePreprocessor(),
            ImageExtension(),
            MetaDataExtension(),
#            RawLinkExtension(),
            ReferencesIdExtension(),
            StylingExtension()
        ],
        extension_configs={"footnotes": {"PLACE_MARKER" : "///Footnotes///"}},
    )

    # html = html.replace('<p>', '<p style="text-align: justify;">')
    return html


if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    html = process(infile)
    with open(outfile, "w") as f:
        f.write(html)
