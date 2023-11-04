''' This module implements Hash-a-matic commands '''
from __future__ import annotations

import argparse
import glob
import importlib
import logging
import os
import random
from argparse import ArgumentParser
from functools import partialmethod
from typing import Dict, List, Optional
from PIL.Image import Image


class BotResult():
    def __init__(
        self,
        image: Optional[Image] = None,
        text: str = "",
        tags: Optional[List[str]] = None,
        alt_text: Optional[str] = None
    ) -> None:
        self.image = image
        self.text = str(text)
        self.alt_text = alt_text
        if tags:
            self.tags = tags
        else:
            self.tags = []

    def __str__(self) -> str:
        ret = ""
        if self.image:
            ret += f" Has Image ({self.alt_text})\n"
        ret += f" Text: {self.text}\n"
        if self.tags:
            ret += f" Tags: {' '.join(sorted(self.tags))}\n"
        return ret.strip()


class iRandom:
    ''' inherit from this if your class can be run as a random choice with no input '''


class BotCmd():
    ''' This base class specifies an Interface for commands '''

    commands: Dict[str, BotCmd] = {}  # cls variable

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("_"):
            cls.commands[cls.__name__] = cls

    def __init__(self, private: bool = False) -> None:
        self.private = private

    def run(self, _args: argparse.Namespace) -> BotResult:
        ''' this runs the command '''
        raise NotImplementedError

    def random(self) -> BotResult:
        ''' This returns a random result - overload if you need specfic arguments '''
        parser = self.add_argparse_arguments(ArgumentParser())
        args = parser.parse_args("".split())
        return self.run(args)

    @staticmethod
    def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
        ''' given an ArgumentParser add any parameters needed for this command '''
        return parser

    @classmethod
    def build_subparsers(cls, parser: argparse.ArgumentParser) -> ArgumentParser:
        ''' this function takes a parser and adds sub parsers for all the BotCmds '''
        subparsers = parser.add_subparsers(title="Bot Commands", required=True, dest="botCommand")
        for cmd, cmdclass in sorted(cls.commands.items()):
            subparser = subparsers.add_parser(cmd.lower(), help=cmdclass.__doc__)
            subparser.set_defaults(botcmd=cmdclass)
            cmdclass.add_argparse_arguments(subparser)
        return parser

    @classmethod
    def runner(cls, args: argparse.Namespace) -> BotResult:
        botcmd: BotCmd = args.botcmd()
        return botcmd.run(args)

    @classmethod
    def get_choices(cls, api: Optional[type] = None) -> List[str]:
        ret = []
        for (cmd, cmd_class) in cls.commands.items():
            if not api or issubclass(cmd_class, api):  # type: ignore
                ret.append(cmd)
        return ret

    random_choices = partialmethod(get_choices, iRandom)


class Random(BotCmd):
    ''' A Random choice from the other commands '''

    tags: List[str] = ["art", "botArt"]

    def run(self, args: argparse.Namespace) -> BotResult:
        choices = BotCmd.random_choices()
        if choices:
            cmd = random.choice(choices)
            cmdclass = BotCmd.commands[cmd]
            logging.debug(f"Random Choice {cmd}")
            result = cmdclass().random()  # type: ignore
            result.tags.append("random")
            return result
        return BotResult(text="No Commands Support Random")


# find and import all other modules in this folder
for f in glob.glob(os.path.join(
    os.path.dirname(__file__),
    "*.py"
)):
    m = os.path.basename(f)
    if m.startswith("_"):
        continue
    try:
        logging.debug("Loading Cmd: %s", m)
        importlib.import_module("." + os.path.splitext(m)[0], __package__)
    except ImportWarning as e:
        logging.warning("%s: %s", m.rsplit(".", 1)[0], str(e))
    except ImportError as e:
        logging.error("Failed to import command '%s': %s", m.rsplit(".", 1)[0], e.msg)
