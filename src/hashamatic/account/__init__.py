''' This module implements various hashamatic accounts '''

from __future__ import annotations

import glob
import importlib
import logging
import os
from functools import partialmethod
from typing import Dict, List, Optional

from hashamatic.command import BotResult


class iPost():   # pylint:disable=invalid-name
    ''' interface class if you support posting '''

    def post(self, post: BotResult) -> bool:
        ''' Implement posting here '''
        raise NotImplementedError


class iMessage():  # pylint:disable=invalid-name
    ''' interface class if you support sending direct messages'''

    def message(self, user: str, message: BotResult) -> bool:
        ''' Implement messaging here '''
        raise NotImplementedError


class BotAccount():
    ''' This base class specifies an Interface for posting to services '''

    accounts: Dict[str, BotAccount] = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            cls.accounts[cls.__name__.lower()] = cls()

    @classmethod
    def get_choices(cls, api: Optional[type] = None) -> List[str]:
        ''' return the list of valid accounts '''
        ret = []
        for (acc, acc_class) in cls.accounts.items():
            if not api or isinstance(acc_class, api):
                ret.append(acc)
        return ret

    post_choices = partialmethod(get_choices, iPost)
    message_choices = partialmethod(get_choices, iMessage)

    @classmethod
    def default(cls) -> BotAccount:
        ''' return the default account (echo) '''
        return cls.accounts['echo']


class Echo(BotAccount, iPost, iMessage):
    ''' A simple "echo to stdout" BotAccount '''

    logger = logging.getLogger("Echo")

    def post(self, post: BotResult) -> bool:
        print("Post:")
        if post.image:
            print(f" Has Image ({post.alt_text})")
            show = input("Display? y/N:").lower()
            if show.startswith("Y"):
                post.image.show()

        print(f" Text: {post.text}")
        if post.tags:
            print(f" Tags: {' '.join(sorted(post.tags))}")
        return True

    def message(self, user: str, message: BotResult) -> bool:
        print(f"Msg To: {user}")
        if message.image:
            print(f" Has Image ({message.alt_text})")
            filename = input("Save File As [don't save]:").strip()
            if filename:
                message.image.save(filename)
        print(f"Text: {message.text}")
        return True


# find and import all other modules in this folder
for f in glob.glob(os.path.join(
    os.path.dirname(__file__),
    "*.py"
)):
    m = os.path.basename(f)
    if m.startswith("_"):
        continue
    try:
        logging.debug("Loading Account: %s", m)
        importlib.import_module("." + os.path.splitext(m)[0], __package__)
    except ImportWarning as e:
        logging.warning("%s: %s", m.rsplit(".", 1)[0], str(e))
    except ImportError as e:
        logging.error(
            "Failed to import account handler '%s': %s",
            m.rsplit(".", 1)[0], e.msg
        )
