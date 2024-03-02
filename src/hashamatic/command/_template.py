import logging
from argparse import ArgumentParser, Namespace
from typing import List

from PIL.Image import new as NewImage
# from PIL.Image import Image
# from PIL import ImageDraw

try:
    from hashamatic.command import BotCmd, BotResult

    class CMD(BotCmd):
        ''' what this cmd produces '''

        tags: List[str] = ["art", "botArt"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            return parser

        def run(self, _args: Namespace) -> BotResult:
            imageRaw = NewImage('rgba', (128, 128))
            return BotResult(imageRaw, tags=self.tags)

        def random(self) -> BotResult:
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args("".split())
            return self.run(args)

except ImportError:
    logging.debug("failed to import BotCmd interface")
