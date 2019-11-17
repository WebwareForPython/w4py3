"""Default base class for PSP pages.

This class is intended to be used in the future as the default base class
for PSP pages in the event that some special processing is needed.
Right now, no special processing is needed, so the default base class
for PSP pages is the standard Webware Page.
"""

from Page import Page


class PSPPage(Page):

    def __init__(self):
        self._parent = Page
        self._parent.__init__(self)

    def awake(self, transaction):
        self._parent.awake(self, transaction)
        self.out = transaction.response()
