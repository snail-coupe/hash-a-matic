''' Implement a Maze command '''
from __future__ import annotations

import collections
import collections.abc
import logging
import random
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Sequence, Tuple, Union, Optional

from PIL import ImageDraw, ImageFont
from PIL.Image import Image
from PIL.Image import new as NewImage

try:
    from hashamatic.command import BotCmd, BotResult, iRandom

    class _Maze(BotCmd):
        ''' Maze Command '''

        tags: List[str] = ["maze", "fractal", "brainTraining"]
        caption = "Can you find your way through my maze?"

        def run(self, _args: Namespace) -> BotResult:
            ''' this runs the command '''
            raise NotImplementedError

    class Maze(_Maze, iRandom):
        ''' A Random Maze '''

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("rows", type=int, nargs='?', default=None)
            parser.add_argument("columns", type=int, nargs='?', default=None)
            return parser

        def run(self, args: Namespace) -> BotResult:
            cols = args.columns
            rows = args.rows
            if not rows:
                rows = random.randint(12, 32)
            else:
                rows = max(rows, 1)
                rows = min(rows, 64)
            if not cols:
                cols = rows
            else:
                cols = max(cols, 1)
                cols = min(cols, 120)
            maker = MazeMaker(width=cols, height=rows)
            maker.generate()
            image_raw = maker.render(16)
            return BotResult(
                image_raw, text=self.caption, tags=self.tags,
                alt_text=f"A computer generated {rows} by {cols} maze."
            )

        def random(self) -> BotResult:
            size = random.randint(12, 32)
            parser = self.add_argparse_arguments(ArgumentParser())
            args = parser.parse_args(f"{size}".split())
            return self.run(args)

    class HeartMaze(_Maze):
        ''' A Random Maze around a Heart '''

        tags = _Maze.tags + ["❤️"]

        h = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            return parser

        def run(self, _args: Namespace) -> BotResult:
            maker = MazeMaker(23, 23)
            maker.apply_shape(self.h, 4, 4)
            img = maker.generate().render(16)
            return BotResult(
                img, text=self.caption, tags=self.tags,
                alt_text="A computer generated 23 by 23 maze with a heart in the middle."
            )

    class TextMaze(_Maze):
        ''' A Random Maze around some text '''

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("word", type=str, nargs='+')
            return parser

        def run(self, args: Namespace) -> BotResult:
            maker = MazeMaker.from_text(args.word, 4)
            img = maker.generate().render(8)
            return BotResult(
                img, text=self.caption, tags=self.tags,
                alt_text=f"A computer generated {maker.height} by {maker.width} maze, containing the text: {args.word}."
            )

    class EmojiMaze(_Maze):
        ''' A Random Maze around an emoji '''

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("emoji", type=str)
            return parser

        def run(self, args: Namespace) -> BotResult:
            maker = MazeMaker.from_emoji(args.emoji, 8)
            img = maker.generate().render(8)
            return BotResult(
                img, text=self.caption, tags=self.tags + [args.emoji],
                alt_text=f"A computer generated {maker.height} by {maker.width} maze, containing the emoji: {args.emoji}."
            )

except ImportError:
    logging.debug("failed to import BotCmd interface")


class MazeCell():
    ''' represents one cell within the maze '''
    def __init__(self):
        self.solid = False
        self.visited = False
        self.right = self.left = self.top = self.bottom = True

    def __str__(self):
        bits = 0
        if self.left:
            bits = bits + 1
        if self.right:
            bits = bits + 2
        if self.top:
            bits = bits + 4
        if self.bottom:
            bits = bits + 8
        return f"{bits:4b}"


class MazeMaker():
    '''
        https://en.wikipedia.org/wiki/Maze_generation_algorithm '''

    def __init__(self, width: int = 48, height: Optional[int] = None):
        self.width = self.height = width
        if height:
            self.height = height
        self.maze: Dict[Tuple[int, int], MazeCell] = collections.defaultdict(MazeCell)

    @classmethod
    def from_text(cls, text: Union[Sequence[str], str], padding: int) -> MazeMaker:
        ''' generates a MazeMaker containing text '''
        if isinstance(text, collections.abc.Sequence):
            if len(text) > 3:
                text = text[:3]
            text = "\n".join(text)
        fnt = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf', 32)
        (left, top, right, bottom) = ImageDraw.Draw(NewImage('1', (1, 1))).multiline_textbbox((0, 0), text, font=fnt)
        logging.debug("%d %d %d %d", left, top, right, bottom)
        maker = cls(right + 2 * padding, bottom + 2 * padding)
        im = NewImage('1', (right + 2 * padding, bottom + 2 * padding))
        d = ImageDraw.Draw(im)
        d.multiline_text((padding + 1, padding), text, 1, font=fnt, align='center')
        px = im.load()
        for xpos in range(0, right + 2 * padding):
            for ypos in range(0, bottom + 2 * padding):
                if px[xpos, ypos]:
                    maker.maze[(xpos, ypos)].visited = True
                    maker.maze[(xpos, ypos)].solid = True
        return maker

    @classmethod
    def from_emoji(cls, emoji: str, padding: int) -> MazeMaker:
        ''' returns a MazeMaker that makes a maze around an emoji '''
        fnt = ImageFont.truetype('/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf', 48)
        (left, top, right, bottom) = ImageDraw.Draw(NewImage('1', (1, 1))).multiline_textbbox((0, 0), emoji[:1], font=fnt)
        logging.debug("%d %d %d %d", left, top, right, bottom)
        maker = cls(right + 2 * padding, bottom + 2 * padding)
        im = NewImage('1', (right + 2 * padding, bottom + 2 * padding))
        d = ImageDraw.Draw(im)
        d.multiline_text((padding + 1, padding), emoji, 1, font=fnt, align='center')
        px = im.load()
        for xpos in range(0, right + 2 * padding):
            for ypos in range(0, bottom + 2 * padding):
                if px[xpos, ypos]:
                    maker.maze[(xpos, ypos)].visited = True
                    maker.maze[(xpos, ypos)].solid = True
        return maker

    def apply_shape(self, shape: List[List[int]], xos, yos):
        ''' applies the supplied shape as a solid section of maze '''
        for ypos, xdata in enumerate(shape):
            for xpos, solid in enumerate(xdata):
                if solid:
                    self.maze[(xpos + xos + 1, ypos + yos + 1)].visited = True
                    self.maze[(xpos + xos + 1, ypos + yos + 1)].solid = True

    def get_cell(self, xos: int, yos: int) -> MazeCell:
        if not self.maze[(xos, yos)].visited:
            self.generate(xos, yos)
        return self.maze[(xos, yos)]

    def generate(self, xpos=1, ypos=1):
        # set up
        stack = list()
        self.maze[(xpos, ypos)].visited = True
        stack.append((xpos, ypos))

        # run
        while stack:
            choices = list()
            valid_choices = list()
            if xpos > 1:
                choices.append((xpos - 1, ypos))
            if xpos < self.width:
                choices.append((xpos + 1, ypos))
            if ypos > 1:
                choices.append((xpos, ypos - 1))
            if ypos < self.height:
                choices.append((xpos, ypos + 1))
            for choice in choices:
                if not self.maze[choice].visited:
                    valid_choices.append(choice)
            if not valid_choices:
                (xpos, ypos) = stack.pop()
                continue
            (new_x, new_y) = random.choice(valid_choices)
            self.maze[(new_x, new_y)].visited = True
            if new_x < xpos:
                self.maze[(new_x, new_y)].right = self.maze[(xpos, ypos)].left = False
            elif new_x > xpos:
                self.maze[(new_x, new_y)].left = self.maze[(xpos, ypos)].right = False
            elif new_y < ypos:
                self.maze[(new_x, new_y)].bottom = self.maze[(xpos, ypos)].top = False
            elif new_y > ypos:
                self.maze[(new_x, new_y)].top = self.maze[(xpos, ypos)].bottom = False
            else:
                raise Exception("How did you get here?????")
            (xpos, ypos) = (new_x, new_y)
            stack.append((xpos, ypos))
        return self

    def render(self, cell_size: int = 16) -> Image:
        img = NewImage("RGB", (
            self.width * cell_size, self.height * cell_size
        ))
        draw = ImageDraw.Draw(img)

        floor_color = "rgb(%d,%d,%d)" % (
            random.choice(range(128, 256)),
            random.choice(range(128, 256)),
            random.choice(range(128, 256))
        )
        for xos in range(0, self.width):
            for yos in range(0, self.height):
                cell = self.get_cell(xos + 1, yos + 1)
                xcs = xos * cell_size
                ycs = yos * cell_size
                if not cell.solid:
                    draw.rectangle((
                        (xcs + 1, ycs + 1),
                        (xcs + cell_size - 2, ycs + cell_size - 2)
                    ), floor_color)
                if not cell.left:
                    draw.rectangle(((xcs, ycs + 1), (xcs + 1, ycs + cell_size - 2)), floor_color)
                if not cell.right:
                    draw.rectangle(((xcs + cell_size - 2, ycs + 1), (xcs + cell_size - 1, ycs + cell_size - 2)), floor_color)
                if not cell.top:
                    draw.rectangle(((xcs + 1, ycs), (xcs + cell_size - 2, ycs + 1)), floor_color)
                if not cell.bottom:
                    draw.rectangle(((xcs + 1, ycs + cell_size - 2), (xcs + cell_size - 2, ycs + cell_size - 1)), floor_color)
        draw.regular_polygon(
            (cell_size / 2, cell_size / 2, cell_size / 2),
            n_sides=5,
            fill="rgb(0,192,0)",
            rotation=-90
        )
        draw.regular_polygon(
            (self.width * cell_size - cell_size / 2, self.height * cell_size - cell_size / 2, cell_size / 2),
            n_sides=5,
            fill="rgb(192,0,0)",
            rotation=90
        )

        return img

    def render_as_mask(self, cell_size: int = 16) -> Image:
        mask = NewImage("1", (
            self.width * cell_size, self.height * cell_size
        ))
        draw = ImageDraw.Draw(mask)

        for xos in range(0, self.width):
            for yos in range(0, self.height):
                cell = self.get_cell(xos + 1, yos + 1)
                xcs = xos * cell_size
                ycs = yos * cell_size
                draw.rectangle((
                    (xcs + 1, ycs + 1),
                    (xcs + cell_size - 2, ycs + cell_size - 2)
                ), True)
                if not cell.left:
                    draw.rectangle(((xcs, ycs + 1), (xcs + 1, ycs + cell_size - 2)), True)
                if not cell.right:
                    draw.rectangle(((xcs + cell_size - 2, ycs + 1), (xcs + cell_size - 1, ycs + cell_size - 2)), True)
                if not cell.top:
                    draw.rectangle(((xcs + 1, ycs), (xcs + cell_size - 2, ycs + 1)), True)
                if not cell.bottom:
                    draw.rectangle(((xcs + 1, ycs + cell_size - 2), (xcs + cell_size - 2, ycs + cell_size - 1)), True)

        return mask


if __name__ == "__main__":
    t = MazeMaker(32, 32)
    i = t.render(16)
    i.save("temp.png", "PNG")
