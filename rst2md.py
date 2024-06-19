# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import typing as ty

from docutils import frontend
from docutils import nodes
from docutils.parsers import rst as rst_parser
from docutils import utils

RetType = ty.Generator[str, None, None]


class UnsupportedNode(Exception):
    def __init__(self, node: nodes.Node):
        message = f'unsupported node type {type(node)!r}, data={node}'
        super().__init__(message)


def _convert_text(text: nodes.Text, *, join=True) -> RetType:
    ret = text.astext()
    if join:
        ret = ret.replace('\n', ' ')
    yield ret


def _convert_literal(literal: nodes.literal) -> RetType:
    yield f'`{literal.astext()}`'


def _convert_emphasis(emphasis: nodes.emphasis) -> RetType:
    yield f'*{emphasis.astext()}*'


def _convert_strong(strong: nodes.strong) -> RetType:
    yield f'**{strong.astext()}**'


def _convert_image(image: nodes.image) -> RetType:
    alt = image.attributes.get('alt') or 'image'
    uri = image.attributes['uri']
    yield f'![{alt}]({uri})'


def _convert_reference(reference: nodes.reference) -> RetType:
    if 'name' in reference.attributes:  # text reference
        name = reference.attributes['name']
        # TODO(stephenfin): If refuri is not set, this is a reference-style
        # URL. We need global state to resolve this.
        uri = reference.attributes.get('refuri') or '#'
        yield f'[{name}]({uri})'
    elif isinstance(reference[0], nodes.image):  # image reference
        yield from _convert_image(reference[0])
    elif isinstance(reference[0], str):  # plain URL
        yield reference.attributes['refuri']
    else:
        raise UnsupportedNode(reference)


def _convert_title(title: nodes.title) -> RetType:
    yield f'# {title.astext()}\n'


def _convert_title_reference(
    title_reference: nodes.title_reference,
) -> RetType:
    # TODO(stephenfin): We should (potentially) point to a title but we need to
    # resolve these first
    yield f'{title_reference.astext()}'


def _convert_section(section: nodes.section) -> RetType:
    for node in section:
        if isinstance(node, nodes.section):
            # TODO(stephenfin): Here we'd want to increase section level (for
            # things like headers)
            yield from _convert_section(node)
        elif isinstance(node, nodes.title):
            yield from _convert_title(node)
        elif isinstance(node, nodes.paragraph):
            yield from _convert_paragraph(node)
        elif isinstance(node, nodes.bullet_list):
            yield from _convert_bullet_list(node)
        elif isinstance(node, nodes.literal_block):
            yield from _convert_literal_block(node)
        elif isinstance(node, nodes.block_quote):
            yield from _convert_block_quote(node)
        elif isinstance(node, nodes.reference):
            yield from _convert_reference(node)
        elif isinstance(node, nodes.target):
            # TODO(stephenfin): We should keep track of these
            pass
        elif isinstance(node, nodes.comment):
            pass  # ignored
        else:
            raise UnsupportedNode(node)
        yield '\n'


def _convert_paragraph(paragraph: nodes.paragraph) -> RetType:
    for node in paragraph:
        if isinstance(node, nodes.Text):
            yield from _convert_text(node)
        elif isinstance(node, nodes.literal):
            yield from _convert_literal(node)
        elif isinstance(node, nodes.strong):
            yield from _convert_strong(node)
        elif isinstance(node, nodes.emphasis):
            yield from _convert_emphasis(node)
        elif isinstance(node, nodes.reference):
            yield from _convert_reference(node)
        elif isinstance(node, nodes.target):
            # TODO(stephenfin): We should keep track of these
            pass
        elif isinstance(node, nodes.title_reference):
            yield from _convert_title_reference(node)
        else:
            raise UnsupportedNode(node)
    yield '\n'


def _convert_list_item(list_item: nodes.list_item) -> RetType:
    prefix = '- '
    for node in list_item:
        yield prefix
        if isinstance(node, nodes.paragraph):
            yield from _convert_paragraph(node)
        else:
            raise UnsupportedNode(node)
        prefix = '\n  '


def _convert_bullet_list(bullet_list: nodes.bullet_list) -> RetType:
    for node in bullet_list:
        if isinstance(node, nodes.list_item):
            yield from _convert_list_item(node)
        else:
            raise UnsupportedNode(node)


def _convert_literal_block(literal_block: nodes.literal_block) -> RetType:
    yield '```\n'
    for node in literal_block:
        if isinstance(node, nodes.Text):
            yield from _convert_text(node, join=False)
        else:
            raise UnsupportedNode(node)
        yield '\n'
    yield '```\n'


def _convert_block_quote(block_quote: nodes.block_quote) -> RetType:
    for node in block_quote:
        yield '> '
        if isinstance(node, nodes.paragraph):
            yield from _convert_paragraph(node)
        elif isinstance(node, nodes.bullet_list):
            yield from _convert_bullet_list(node)
        else:
            raise UnsupportedNode(node)


def _convert_document(document: nodes.document) -> RetType:
    for node in document:
        if isinstance(node, nodes.section):
            yield from _convert_section(node)
        elif isinstance(node, nodes.paragraph):
            yield from _convert_paragraph(node)
        elif isinstance(node, nodes.bullet_list):
            yield from _convert_bullet_list(node)
        elif isinstance(node, nodes.literal_block):
            yield from _convert_literal_block(node)
        else:
            raise UnsupportedNode(node)
        yield '\n'


def convert_rst_to_md(name: str, data: str) -> str:
    """Convert a reStructuredText document to Markdown.

    This is massively incomplete but (famous last words) it should be good
    enough for our purposes.

    :param name: The name of the source document.
    :param data: The contents of the source document.
    :returns: The converted document.
    """
    settings = frontend.get_default_settings(rst_parser.Parser)

    document = utils.new_document(name, settings)
    rst_parser.Parser().parse(data, document)

    return ''.join(_convert_document(document)).strip()


if __name__ == '__main__':
    import argparse
    import pathlib

    parser = argparse.ArgumentParser(
        prog='python -m rst2md',
        description='A utility to convert rST to Markdown',
    )
    parser.add_argument(
        'path',
        type=pathlib.Path,
        help='Path to reStructuredText file to convert',
    )
    args = parser.parse_args()
    with args.path.open('r') as f:
        data = f.read()

    print(convert_rst_to_md(args.path.name, data))
