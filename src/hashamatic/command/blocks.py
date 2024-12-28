''' Hashamatic module to generate packings of squares '''

import collections
import logging
import random
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Tuple, Set

from PIL import ImageDraw
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom, iWallpaper

    class Blocks(BotCmd, iRandom, iWallpaper):
        ''' A packing of various sized coloured squares into a grid. '''

        tags: List[str] = ["squares", "🔲", "ProcGen", "art", "botArt"]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("rows", type=int, nargs='?')
            parser.add_argument("columns", type=int, nargs='?')
            return parser

        def run(self, args: Namespace) -> BotResult:
            cols = args.columns
            rows = args.rows
            if not rows:
                rows = random.randint(12, 32)
            else:
                rows = max(rows, 1)
                rows = min(rows, 65)
            if not cols:
                cols = rows
            else:
                cols = max(cols, 1)
                cols = min(cols, 65)

            b = BlocksMaker(rows, cols)
            alt_text = [f"A computer generated picture of multicoloured squares of various sizes packed into a {cols} by {rows} grid"]
            raw_image = b.generate().render()

            return BotResult(
                raw_image, tags=self.tags,
                alt_text=" ".join(alt_text)
            )

        def random(self) -> BotResult:
            size = random.randint(12, 32)
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args(f"{size}".split())
            return self.run(args)

        def wallpaper(self) -> BotResult:
            b = BlocksMaker(20, 9, 120, 6)
            b.generate()
            raw_image = b.render()
            return BotResult(
                raw_image, tags=self.tags,
                alt_text=f"A computer generated picture of multicoloured squares of various sizes packed into a {b.columns} by {b.rows} grid"
            )

except ImportError:
    logging.debug("failed to import BotCmd interface")

# first define a grid of 1x1 squares
# then iterate over each square:
#     1 in probs chance of enterig growth stage
#     if in growth stage repeat maxs-1 times:
#         if room to grow:
#             1 in probi chance of growing by 1


class BlocksMaker():
    ''' generate packings of random sized and coloured blocks '''

    map: Dict[int, Dict[int, str]] = collections.defaultdict(dict)
    # maxs = 5  # max square size
    probs = 7  # 1:x chance of seed square entering growth
    probi = 2  # 1:x chance of growing each pass of growth iteration

    def __init__(
        self,
        rows: int = 10, columns: int = 10,
        block_size: int = 80,
        border_width: int = 4,
    ):
        self.rows = rows
        self.columns = columns
        self.maxs = min(rows, columns) >> 2
        self.block_size = block_size
        self.border_width = border_width

    def generate(self):
        ''' generate the cells '''

        self.map = collections.defaultdict(dict)
        for r in range(-1, 1 + self.rows):
            for c in range(-1, 1 + self.columns):
                self.map[r][c] = None
        for r in range(self.rows):
            for c in range(self.columns):
                if self.map[r][c]:
                    continue
                s = 1
                if not random.choice(range(self.probs)):
                    for _ in range(1, self.maxs):
                        if (c + s) < self.columns and (r + s) < self.rows:
                            if self.map[r + s + 1][c] or self.map[r][c + s + 1]:
                                continue
                            if not random.choice(range(self.probi)):
                                s = s + 1
                for x in range(s):
                    for y in range(s):
                        self.map[r + y][c + x] = f"{s}:{r}:{c}"
        return self

    def render(self) -> Image:
        ''' render the cells as an image'''

        bs = self.block_size
        bw = self.border_width
        img = NewImage("RGB", (
            bs * self.columns, bs * self.rows
        ))
        draw = ImageDraw.Draw(img)
        for r in range(self.rows):
            for c in range(self.columns):
                if f":{r}:{c}" in self.map[r][c]:
                    s = int(self.map[r][c][0])
                    draw.rectangle((
                        (c * bs + bw, r * bs + bw),
                        ((c + s) * bs - bw, (r + s) * bs - bw)
                    ), "rgb(%d,%d,%d)" % (
                        random.choice(range(256)),
                        random.choice(range(256)),
                        random.choice(range(256))
                    ))
        return img

    def render5colour(self, colours: List[str]) -> Image:
        ''' render the cells as an image using only 5 colours '''

        pivotmap: Dict[int, List[Tuple[int, int]]] = collections.defaultdict(list)
        colormap: Dict[Tuple[int, int], int] = {}

        # empty colour map
        for r in range(-1, self.rows+1):
            for c in range(-1, self.columns+1):
                colormap[(r, c)] = 0

        # build up lists of squares by size
        for r in range(self.rows):
            for c in range(self.columns):
                if f":{r}:{c}" in self.map[r][c]:
                    s = int(self.map[r][c][0])
                    pivotmap[s].append((r, c))

        # work out colours
        colorrange = set(range(1, len(colours)+1))
        for s in sorted(pivotmap.keys(), reverse=True):
            for (r, c) in pivotmap[s]:
                seen: Set[int] = set()
                for rr in range(r, r+s):
                    seen.add(colormap[(rr, c-1)])
                    seen.add(colormap[(rr, c+s)])
                for cc in range(c, c+s):
                    seen.add(colormap[(r-1, cc)])
                    seen.add(colormap[(r+s, cc)])
                choices = list(colorrange - seen)
                if not choices:
                    raise ValueError("Something went wrong, no colours left")
                color = random.choice(choices)
                # print(seen, choices, color)
                for rr in range(r, r+s):
                    for cc in range(c, c+s):
                        colormap[(rr, cc)] = color

        bs = self.block_size
        bw = self.border_width
        img = NewImage("RGB", (
            bs * self.columns, bs * self.rows
        ))
        draw = ImageDraw.Draw(img)

        for s, slist in pivotmap.items():
            for (r, c) in slist:
                draw.rectangle((
                    (c * bs + bw, r * bs + bw),
                    ((c + s) * bs - bw, (r + s) * bs - bw)
                ), colours[colormap[(r, c)]-1])
        return img

    def render_as_mask(self) -> Image:
        ''' rander the cells as 1bit image suitable for use as a mask '''

        bs = self.block_size
        bw = self.border_width
        mask = NewImage("1", (
            bs * self.columns, bs * self.rows
        ))
        draw = ImageDraw.Draw(mask)
        for r in range(self.rows):
            for c in range(self.columns):
                if f":{r}:{c}" in self.map[r][c]:
                    s = int(self.map[r][c][0])
                    draw.rectangle((
                        (c * bs + bw, r * bs + bw),
                        ((c + s) * bs - bw, (r + s) * bs - bw)
                    ), True)
        return mask


if __name__ == "__main__":
    # BlocksMaker(20, 9, 120, 6).generate().render().save("temp.png", "PNG")
    from hashamatic.account.mastodon import Mastodon
    bot = Mastodon()
    colors = bot.get_palette()
    # colors = ["#ad831f", "#bf6e40", "#9c77bb", "#8cd9c3", "#a8f0c4"]

    bm = BlocksMaker(random.randint(12, 32), random.randint(12, 32))
    bm.probs = 2
    bm.generate()
    try:
        bm.render5colour(colors).save("temp.png", "PNG")
    except ValueError as e:
        print("fail!")
        print(e)
        bm.render().save("temp.png", "PNG")
