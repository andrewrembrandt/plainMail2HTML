# Author: Amit Ramon <amitrm@users.sourceforge.net>

# This file is part of plainMail2HTML.

# plainMail2HTML is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.

# plainMail2HTML is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with plainMail2HTML.  If not, see
# <http://www.gnu.org/licenses/>.

"""
The MessageProcessor class processes the mail and attaches to in a
HTML part.
"""

import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from plain2html.core.message_utils import convert_text_to_alternative

class MessageTypeError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MessageProcessor(object):

    # def __init__(self, quote_prefix='', html_parser=None):
    def __init__(self, html_parser=None):
        """Initialize the instance.
        """
        # self.quote_prefix = quote_prefix
        self.html_parser = html_parser

    def generate_html_msg_from_file(self, fp):
        msg = email.message_from_file(fp)
        if msg.is_multipart():
            html_msg =  self._add_html_to_multipart(msg)
        else:
            html_msg = self._add_html_to_plain(msg)

        return html_msg

    def _create_html_message(self, text):
        # parse and convert to HTML
        html = self.html_parser(text)
        html_msg = MIMEText(html, 'html')
        html_msg.set_charset('utf-8')
        return html_msg

    def _add_html_to_plain(self, msg):
        # sanity check
        if msg.is_multipart() or msg.get_content_type() != 'text/plain':
            raise MessageTypeError('Expected text/plain, but got %s.' % \
                                       msg.get_content_type())

        # extract the text body
        text = msg.get_payload(decode=True)

        # create a new multipart/alternative message
        new_msg = convert_text_to_alternative(msg)

        # create and add a text/plain message
        text_part = MIMEText(text, 'plain')
        text_part.set_charset('utf-8')

        html_part = self._create_html_message(text)

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message,
        # in this case the HTML message, is best and preferred.
        new_msg.attach(text_part)
        new_msg.attach(html_part)

        return new_msg

        
    # It is assumed that msg is generated by Mutt, with a known
    # structure. It is multipart/mixed, and the first component is a
    # text/plain message, encoded in utf-8 8-bit.  The first component is
    # replaced by a multipart/alternative message that contains the
    # original first component (text) and a HTML version of it.
    def _add_html_to_multipart(self, msg):
        # sanity check
        if not msg.is_multipart():
            raise MessageTypeError('Expected multipart/alternative, but got %s.' % \
                                       msg.get_content_type())

        # TODO: assert msg is multipart-mix, first part is text-plain
        text_part = msg.get_payload()[0] # text msg is first in list
        if text_part.get_content_type() != 'text/plain':
            raise MessageTypeError('Expected component 1 to be '
                                   'text/plain, but got %s.' % \
                                       msg.get_content_type())

        # extract the text body
        text = text_part.get_payload(decode=True)
        html_part = self._create_html_message(text)

        alt_msg = MIMEMultipart('alternative')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message,
        # in this case the HTML message, is best and preferred.
        alt_msg.attach(text_part)
        alt_msg.attach(html_part)
        msg.get_payload()[0] = alt_msg

        return msg

