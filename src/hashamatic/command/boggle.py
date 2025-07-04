"""Hashamatic module to generate BoggleTM style game boards"""

# Solver Code based upon: https://www.geeksforgeeks.org/boggle-using-trie/
# The code is contributed by Nidhi goel.

# Possible wordlist: https://norvig.com/ngrams/count_1w.txt

import logging
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Set, Dict, Tuple

from random import shuffle, choice, randint
import importlib.resources

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont


class FixedWidth:
    """produce fixed width text"""

    lookup: Dict[str, str] = {}

    lookup["\n"] = "\n"
    lookup[" "] = chr(0x3000)
    for char in range(26):
        lookup[chr(0x41 + char)] = chr(0xFF21 + char)
        lookup[chr(0x61 + char)] = chr(0xFF41 + char)

    @classmethod
    def encode(cls, text: str) -> str:
        """return encoded string"""
        return "".join([cls.lookup[x] for x in text])


def grouper(n: int, s: str) -> list[str]:
    """create list of fixed sized groups from iteratable"""
    return [s[0 + i : n + i] for i in range(0, len(s), n)]


try:
    from hashamatic.command import BotCmd, BotResult

    class Griddle(BotCmd):
        """produces a boggle style word grid"""

        tags: List[str] = ["WordGame", "WordGrid", "brainTraining"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("--solve", nargs="+", type=str)
            parser.add_argument("--game", choices=dicesets.keys())
            parser.add_argument("--minlen", type=int, default=3)
            return parser

        def run(self, args: Namespace) -> BotResult:
            if args.game:
                game = Boggle(dice=args.game)
            elif args.solve:
                game = Boggle(force=[x.upper() for x in args.solve])
            else:
                game = Boggle()
            words = game.solve(args.minlen)
            post = BotResult(
                image=game.render(),
                alt_text=" ".join(
                    [
                        f"Image version of the {game.width} by {game.height} word grid,",
                        "with some letters rotated",
                    ]
                ),
                text="".join(
                    [
                        f"\n{game}\n\n",
                        f"I found {len(words)} words.\n",
                        f"Longest {max([len(x) for x in words])}.\n",
                        f"Target {int(len(words) * 2 / 3)}.\n",
                    ]
                ),
                tags=self.tags,
            )
            text = ", ".join(sorted(list(words)))
            while text:
                if len(text) > 450:
                    split = text[:450].rindex(", ")
                else:
                    split = len(text)
                post.append(
                    BotResult(text=text[:split], warning="Spoiler: My solution")
                )
                text = text[split + 2 :]

            return post

        def random(self) -> BotResult:
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args("".split())
            return self.run(args)

except ImportError:
    logging.debug("failed to import BotCmd interface")


dicesets: Dict[str, Tuple[int, int, List[str]]] = {}
dicesets["standard"] = (
    4,
    4,
    [
        "AACIOT",
        "ABILTY",
        "ABJMOQ",
        "ACDEMP",
        "ACELRS",
        "ADENVZ",
        "AHMORS",
        "BIFORX",
        "DENOSW",
        "DKNOTU",
        "EEFHIY",
        "EGKLUY",
        "EGINTV",
        "EHINPS",
        "ELPSTU",
        "GILRUW",
    ],
)
dicesets["super"] = (5, 5, dicesets["standard"][2].copy())
dicesets["super"][2].extend(
    [
        "AAEEGN",
        "ACHOPS",
        "AFFKPS",
        "DEILRX",
        "DELRVY",
        "EEGHNW",
        "EIOSST",
        "HIMNQU",
        "HLNNRZ",
    ]
)


class Boggle:
    """generate boggle boards"""

    font: Optional[PIL.Image.Image] = None
    grid: List[str]

    def __init__(self, dice: str = "standard", force: Optional[List[str]] = None):
        if force:
            self.grid = force
            self.width = len(force[0])
            self.height = len(force)
        else:
            self.width, self.height, self.dice = dicesets[dice]
            self.shuffle()
        if not self.font:
            self.font = self.loadfont()

    @staticmethod
    def loadfont() -> PIL.Image.Image:
        """loads the font image from the resources"""
        fontfp = (
            importlib.resources.files("hashamatic.resources")
            .joinpath("boggle_font.png")
            .open("rb")
        )
        font = PIL.Image.open(fontfp)
        font.load()
        return font

    def __str__(self) -> str:
        return FixedWidth.encode(
            "\n\n".join(["  ".join(list(x)) for x in self.grid]).replace("Q ", "Qu")
        )

    def shuffle(self) -> None:
        """shuffle the dice"""
        shuffle(self.dice)
        faces: list[str] = []
        for die in self.dice:
            faces.append(choice(die))
        self.grid = ["".join(x) for x in grouper(self.width, "".join(faces))]

    def render_retro(self) -> PIL.Image.Image:
        """render the current grid as an image"""
        img = PIL.Image.new("RGB", (24 * self.width, 24 * self.height), "orange")
        if not self.font:
            self.font = self.loadfont()

        for row in range(self.height):
            for col in range(self.width):
                letter = ord(self.grid[row][col]) - ord("A")
                letter_img = self.font.crop((16 * letter, 0, 16 * letter + 18, 18))
                letter_img = letter_img.rotate(90 * randint(0, 4))
                img.paste(letter_img, (6 + col * 22, 6 + row * 22))
        return img.resize((96 * self.width, 96 * self.height), resample=0)

    def render(self) -> PIL.Image.Image:
        """render the current grid as an image"""
        img = PIL.Image.new("RGB", (96 * self.width, 96 * self.height), "#406060")
        font = PIL.ImageFont.truetype("DejaVuSansMono", 54)
        for row in range(self.height):
            for col in range(self.width):
                letter_img = PIL.Image.new("RGB", (72, 72))
                draw = PIL.ImageDraw.Draw(letter_img)
                letter = self.grid[row][col]
                if letter == "Q":
                    letter = "Qu"
                draw.text((36, 36), letter, anchor="mm", fill="lightgrey", font=font)  # type: ignore
                # rotate letter, bias to right way up.
                letter_img = letter_img.rotate(90 * randint(0, 5))
                img.paste(letter_img, (24 + col * 88, 24 + row * 88))
        return img

    @staticmethod
    def exist(board: List[List[str]], word: str) -> bool:
        """return true if word exists in the board"""
        word = word.replace("QU", "Q")
        for i, j in [(x, y) for x in range(len(board)) for y in range(len(board[0]))]:
            if board[i][j] == word[0] and Boggle.search(board, word, 0, i, j):
                return True
        return False

    @staticmethod
    def search(board: List[List[str]], word: str, length: int, i: int, j: int) -> bool:
        """recursive search for each letter in word"""
        if i not in range(len(board)) or j not in range(len(board[0])):
            return False

        if board[i][j] != word[length]:
            return False

        if length == len(word) - 1:
            return True

        ch = board[i][j]
        board[i][j] = "@"

        ans = (
            Boggle.search(board, word, length + 1, i - 1, j)
            or Boggle.search(board, word, length + 1, i + 1, j)
            or Boggle.search(board, word, length + 1, i, j - 1)
            or Boggle.search(board, word, length + 1, i, j + 1)
            or Boggle.search(board, word, length + 1, i - 1, j + 1)
            or Boggle.search(board, word, length + 1, i - 1, j - 1)
            or Boggle.search(board, word, length + 1, i + 1, j - 1)
            or Boggle.search(board, word, length + 1, i + 1, j + 1)
        )

        board[i][j] = ch
        return ans

    def solve(self, minlen: int) -> Set[str]:
        """solves the current grid"""
        ret: set[str] = set()
        with importlib.resources.path("hashamatic.resources", "words.txt") as wordlist:
            st = {
                x.strip().upper()
                for x in wordlist.read_text(encoding="utf8").splitlines()
                if len(x) >= minlen
            }

        board = [list(x) for x in self.grid]
        for word in st:
            if self.exist(board, word):
                ret.add(word)

        return ret


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    ggame = Boggle()
    # ggame.grid=["GRID","DLE ", "WORD","GAME"]
    # i = ggame.render()
    # i.save("temp.png", "PNG")
    print(ggame.grid)
    print(ggame)
    # print(ggame.solve())
    print(FixedWidth.encode("Hello   Mum"))
