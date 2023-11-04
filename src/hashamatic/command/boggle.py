import logging
from argparse import ArgumentParser, Namespace
from typing import List

from random import shuffle, choice

from itertools import zip_longest

def grouper(n, iterable, padvalue=None):
  "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
  return zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)

try:
    from hashamatic.command import BotCmd, BotResult

    class Griddle(BotCmd):
        ''' produces a boggle style word grid '''

        tags: List[str] = ["WordGame", "WordGrid"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            return parser

        def run(self, args: Namespace) -> BotResult:
            text = "\n".join(Boggle().grid())
            return BotResult(text=text, tags=self.tags)

        def random(self) -> BotResult:
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args("".split())
            return self.run(args)

except ImportError:
    logging.debug("failed to import BotCmd interface")


class Boggle():
    def __init__(self):
        self.dice = [
            "AACIOT", "ABILTY", "ABJMOQu", "ACDEMP", 
            "ACELRS", "ADENVZ", "AHMORS", "BIFORX", 
            "DENOSW", "DKNOTU", "EEFHIY", "EGKLUY", 
            "EGINTV", "EHINPS", "ELPSTU", "GILRUW"
        ]

    def grid(self) -> List[str]:
        shuffle(self.dice)
        faces = []
        for die in self.dice:
            faces.append(choice(die))
        return ["".join(x) for x in grouper(4,faces)]
        


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    logging.info(Boggle().grid())