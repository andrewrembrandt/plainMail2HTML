# plainMail2HTML - Convert a text/plain Email to plain+HTML Email.
#
# Copyright (C) 2016 Amit Ramon <amit.ramon@riseup.net>, Andrew Rembrandt <public@rembrandt.dev>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A markdown parser

Parse markdown text and convert it to HTML. cebn's hibidi code is
used to create directional-aware HTML based on the text language.

Credits: Andrew Rembrandt

"""

import markdown
import re
from plain2html import settings
from plain2html.core.message_utils import indent_quoted_text, load_template, DEFAULT_QUOTE_PATTERN
from plain2html.hibidi import hibidi

def markdown_convert(text):
    """Convert markdown-formatted text into HTML"""
    
    # Ensure quoted lists are handled correctly
    deindented_text = remove_leftmost_indentation(text)
    fixed_text = fix_quoted_lists(deindented_text)

    # Generate the HTML part.
    html_body = markdown.markdown(fixed_text)

    # Insert the body into the template.
    html = load_template(
            settings.HTML_TEMPLATE,
            html_body,
            f"Python-Markdown {markdown.__version__}: https://python-markdown.github.io/")

    # Process the HTML in-place and add BIDI tags based on language
    return hibidi.hibidi_unicode(html)


def remove_leftmost_indentation(text):
    """Convert lists (without the preceding blank line) in quoted text for Markdown"""

    new_lines = []
    lines = text.splitlines(True) # keep end-of-line chars
    quote_pattern = getattr(settings, "QUOTE_PATTERN", DEFAULT_QUOTE_PATTERN)
    quote_with_text_pattern = f"^({ quote_pattern[1:] }[\\t ])([^>\\t ].*)"
    blank_line_with_quote_pattern = f"{ quote_pattern }$"

    bwq_re = re.compile(blank_line_with_quote_pattern)
    q_re = re.compile(quote_with_text_pattern)

    # go over lines, replace quote marks by indentation,
    # add blank lines between different indentation levels.
    indentation = -1
    for line in lines:
        bwq_match = bwq_re.search(line)
        if not bwq_match:
            q_match = q_re.search(line)
            if q_match:
                end_quotes_idx = q_match.group(1).rfind('>')
                start_text_idx = line.index(q_match.group(2))
                cur_indentation = start_text_idx - end_quotes_idx - 1
                if indentation == -1:
                    indentation = cur_indentation
                if cur_indentation < indentation:
                    indentation = cur_indentation

    new_lines = []
    for line in lines:
        bwq_match = bwq_re.search(line)
        if not bwq_match:
            q_match = q_re.search(line)
            if q_match:
                end_quotes_idx = q_match.group(1).rfind('>')
                start_text_idx = line.index(q_match.group(2))
                cur_indentation = start_text_idx - end_quotes_idx - 1
                new_line = line[:end_quotes_idx + 1] + line[end_quotes_idx + 1:cur_indentation - indentation + 2] + line[start_text_idx:]
            else:
                new_line = line
        else:
            new_line = line
            
        new_lines.append(new_line)
    return ''.join(new_lines)


def fix_quoted_lists(text):
    """Convert lists (without the preceding blank line) in quoted text for Markdown"""

    prev_line_is_list = False
    new_lines = []
    lines = text.splitlines(True) # keep end-of-line chars
    quote_pattern = getattr(settings, "QUOTE_PATTERN", DEFAULT_QUOTE_PATTERN)
    quoted_list_pattern = f"({ quote_pattern })" + r"([*+-]+[\t ]|\d+\. )"

    qre = re.compile(quoted_list_pattern)

    # go over lines, replace quote marks by indentation,
    # add blank lines between different indentation levels.
    new_lines = []
    for line in lines:
        match_obj = qre.search(line)
        if not match_obj:
            prev_line_is_list = False
            new_line = line
        else:
            if not prev_line_is_list:
                new_lines.append(match_obj.group(1) + '\n')
            new_line = line
            prev_line_is_list = True
            
        new_lines.append(new_line)

    return ''.join(new_lines)
    
