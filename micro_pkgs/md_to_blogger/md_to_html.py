import requests
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re
import sys
import os
import base64
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter, RawTokenFormatter

class CodeBlockPreprocessor(Preprocessor):
    CODE_BLOCK_RE = re.compile(r'```(?P<language>\w+)?\n(?P<code>.+?)```', re.DOTALL)

    def run(self, lines):
        def repl(m):
            language = m.group('language')
            if language is None:
                language = 'text'
            code = m.group('code')
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(nowrap=True)
            code = highlight(code, lexer, formatter)
            return '\n\n<pre class="language-%s"><code>%s</code></pre>\n\n' % (language, code)
        text = '\n'.join(lines)
        text = self.CODE_BLOCK_RE.sub(repl, text)
        return text.split('\n')

class InlineCodePreprocessor(Preprocessor):
    INLINE_CODE_RE = re.compile(r'`(?P<code>.+?)`', re.DOTALL)

    def run(self, lines):
        def repl(m):
            code = m.group('code').replace('\n', ' ')
            lexer = TextLexer()
            formatter = HtmlFormatter(nowrap=True)
            highlighted_code = highlight(code, lexer, formatter)
            return '<span class="inline-code-highlight">%s</span>' % highlighted_code
        text = '\n'.join(lines)
        text = self.INLINE_CODE_RE.sub(repl, text)
        return text.split('\n')

class ImagePreprocessor(Preprocessor):
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

class CodeBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CodeBlockPreprocessor(md), 'code_block', 175)
        md.preprocessors.register(InlineCodePreprocessor(md), 'inline_code', 150)
        md.preprocessors.register(ImagePreprocessor(md), 'image_preprocessor', 125)


class MetaDataPreprocessor(Preprocessor):
    META_PATTERN = re.compile(r'<!-- META: (.+?) -->')

    def run(self, lines):
        metadata = {}

        for line in lines:
            match = self.META_PATTERN.match(line)
            if match:
                meta_data = match.group(1)
                # Parse the metadata and extract relevant information
                # For example, split by commas to extract tags
                key_values = [item.strip() for item in meta_data.split(',')]
                for key_value in key_values:
                    key, value = key_value.split('=')
                    metadata[key.strip()] = value.strip()
            else:
                break  # Stop processing when encountering non-meta line

        # Store the metadata in some way (e.g., in a global variable, database, etc.)
        print("Metadata:", metadata)

        # Return the remaining lines for further Markdown processing
        return lines[len(metadata) + 1:]

class MetaDataExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(MetaDataPreprocessor(md), 'meta_data', 0)


class RawLinkPreprocessor(Preprocessor):
    # Matches both URLs within markdown links and standalone URLs
    URL_RE = re.compile(r'(\[([^]]+)\]\((https?://[^\s]+)\))|(https?://[^\s]+)')

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
        md.preprocessors.register(RawLinkPreprocessor(md), 'raw_link', 100)


def process(infile):
    with open(infile, 'r') as f:
        text = f.read()
    html = markdown.markdown(text, extensions=[CodeBlockExtension(),
                                                    RawLinkExtension(),
                                                    MetaDataExtension(),
                                                    'fenced_code'])
    html = html.replace('<p>', '<p style="text-align: justify;">')
    return html

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    html = process(infile)
    with open(outfile, 'w') as f:
        f.write(html)
