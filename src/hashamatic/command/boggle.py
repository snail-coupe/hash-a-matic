''' Hashamatic module to generate BoggleTM style game boards '''

# Solver Code based upon: https://www.geeksforgeeks.org/boggle-using-trie/
# The code is contributed by Nidhi goel.

import logging
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Set

from random import shuffle, choice, randint
import importlib.resources

from itertools import zip_longest


import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont


def grouper(n, iterable, padvalue=None):
    ''' create list of fixed sized groups from iteratable '''
    return zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)


try:
    from hashamatic.command import BotCmd, BotResult

    class Griddle(BotCmd):
        ''' produces a boggle style word grid '''

        tags: List[str] = ["WordGame", "WordGrid", "brainTraining"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            return parser

        def run(self, _args: Namespace) -> BotResult:
            game = Boggle()
            words = game.solve()
            return BotResult(
                image=game.render(),
                alt_text=" ".join([
                    "Image version of the 4 by 4 word grid,",
                    "with some letters rotated"
                ]),
                text="".join([
                    f"\n```\n{game}\n```\n",
                    f"I found {len(words)} words.\n",
                    f"Target {int(len(words) * 2 / 3)}\n"
                ]),
                tags=self.tags
            )

        def random(self) -> BotResult:
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args("".split())
            return self.run(args)

except ImportError:
    logging.debug("failed to import BotCmd interface")


class Boggle():
    ''' generate boggle boards '''

    font: Optional[PIL.Image.Image] = None

    def __init__(self):
        self.dice = [
            "AACIOT", "ABILTY", "ABJMOQ", "ACDEMP",
            "ACELRS", "ADENVZ", "AHMORS", "BIFORX",
            "DENOSW", "DKNOTU", "EEFHIY", "EGKLUY",
            "EGINTV", "EHINPS", "ELPSTU", "GILRUW"
        ]
        self.shuffle()
        if not self.font:
            self.font = self.loadfont()

    @staticmethod
    def loadfont() -> PIL.Image.Image:
        ''' loads the font image from the resources '''
        fontfp = importlib.resources.files(
            "hashamatic.resources"
        ).joinpath(
            "boggle_font.png"
        ).open("rb")
        font = PIL.Image.open(fontfp)
        font.load()
        return font

    def __str__(self) -> str:
        board = [" "+" ".join(list(x))+" " for x in self.grid]
        return "\n\n".join(board).replace("Q ", "Qu")

    def shuffle(self) -> None:
        ''' shuffle the dice '''
        shuffle(self.dice)
        faces = []
        for die in self.dice:
            faces.append(choice(die))
        self.grid = ["".join(x) for x in grouper(4, faces)]

    def render_retro(self) -> PIL.Image.Image:
        ''' render the current grid as an image '''
        img = PIL.Image.new("RGB", (96, 96), "orange")
        if not self.font:
            self.font = self.loadfont()

        for row in range(4):
            for col in range(4):
                letter = ord(self.grid[row][col]) - ord('A')
                letter_img = self.font.crop((16*letter, 0, 16*letter+18, 18))
                letter_img = letter_img.rotate(90 * randint(0, 4))
                img.paste(letter_img, (6+col*22, 6+row*22))
        return img.resize((384, 384), resample=0)

    def render(self) -> PIL.Image.Image:
        ''' render the current grid as an image '''
        img = PIL.Image.new("RGB", (384, 384), "#406060")
        font = PIL.ImageFont.truetype("DejaVuSansMono", 54)
        for row in range(4):
            for col in range(4):
                letter_img = PIL.Image.new("RGB", (72, 72))
                draw = PIL.ImageDraw.Draw(letter_img)
                letter = self.grid[row][col]
                if letter == "Q":
                    letter = "Qu"
                draw.text(
                    (36, 36), letter,
                    anchor="mm", fill="lightgrey", font=font
                )
                letter_img = letter_img.rotate(90 * randint(0, 4))
                img.paste(letter_img, (24+col*88, 24+row*88))
        return img

    @staticmethod
    def exist(board: List[List[str]], word: str) -> bool:
        ''' return true if word exists in the board '''
        word = word.replace("QU", "Q")
        for (i, j) in [(x, y) for x in range(4) for y in range(4)]:
            if board[i][j] == word[0] and Boggle.search(board, word, 0, i, j):
                return True
        return False

    @staticmethod
    def search(
        board: List[List[str]], word: str,
        length: int, i: int, j: int
    ) -> bool:
        ''' recursive search for each letter in word '''
        if i < 0 or i >= 4 or j < 0 or j >= 4:
            return False

        if board[i][j] != word[length]:
            return False

        if length == len(word) - 1:
            return True

        ch = board[i][j]
        board[i][j] = '@'

        ans = Boggle.search(board, word, length+1, i-1, j) or \
            Boggle.search(board, word, length+1, i+1, j) or \
            Boggle.search(board, word, length+1, i, j-1) or \
            Boggle.search(board, word, length+1, i, j+1) or \
            Boggle.search(board, word, length+1, i-1, j+1) or \
            Boggle.search(board, word, length+1, i-1, j-1) or \
            Boggle.search(board, word, length+1, i+1, j-1) or \
            Boggle.search(board, word, length+1, i+1, j+1)

        board[i][j] = ch
        return ans

    def solve(self) -> Set[str]:
        ''' solves the current grid '''
        temp = set()
        with importlib.resources.path(
            "hashamatic.resources", "words.txt"
        ) as wordlist:
            st = {
                x.strip().upper()
                for x in wordlist.read_text().splitlines()
            }

        board = [list(x) for x in self.grid]
        for word in st:
            if self.exist(board, word):
                temp.add(word)

        return temp


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    ggame = Boggle()
    logging.info(ggame)
    # ggame.grid=["GRID","DLE ", "WORD","GAME"]
    # i = ggame.render()
    # i.save("temp.png", "PNG")
    print(ggame.solve())
