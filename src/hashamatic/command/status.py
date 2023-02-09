import hashlib
import io
import logging
import os
from typing import Tuple

import requests
from PIL.Image import Image
from speedtest import Speedtest

try:
    from argparse import ArgumentParser, Namespace

    from hashamatic.command import BotCmd, BotResult

    class Hash(BotCmd):
        ''' Guess the hash '''
        def run(self, args: Namespace) -> BotResult:
            r = os.urandom(128)
            m = hashlib.md5()
            m.update(r)
            return BotResult(
                text=m.digest().hex(),
                tags=["hash"]
            )

    class Status(BotCmd):
        ''' Basic status information about the server housing the bot. '''
        def run(self, args: Namespace) -> BotResult:
            return BotResult(text=statusGetter().status())

    class SpeedTest(BotCmd):
        ''' Perform a speedtest of the server housing the bot. '''
        def run(self, args: Namespace) -> BotResult:
            (text, image) = statusGetter().speedtest(args.graphical)
            return BotResult(image=image, text=text)

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("--graphical", "-g", action="store_true")
            return parser

except ImportError:
    logging.debug("failed to import BotCmd interface")


class statusGetter():
    def __init__(self):
        pass

    def friendlyTime(self, t) -> str:
        t = t.__int__()
        sec = t % 60
        t = t / 60
        min = t % 60
        t = t / 60
        hr = t % 24
        t = t / 24
        return "%dd%2.2d:%2.2d:%2.2d" % (t, hr, min, sec)

    def speedtest(self, share=False) -> Tuple[str, Image]:
        s = Speedtest()
        url = None

        upload = s.upload() / 1000 / 1000
        download = s.download() / 1000 / 1000
        ping = s.results.ping
        if share:
            url = s.results.share()
            data = requests.get(url)
            image = Image.open(io.BytesIO(data.content))
        else:
            image = None

        return "Ping: %3.2f\nUpld: %3.2f\nDnld: %3.2f\n" % (
            ping, upload, download,
        ), image

    def status(self) -> str:
        with open('/proc/uptime') as f:
            (uptime, idletime) = [
                (lambda x: float(x))(i) for i in f.readline().split(" ")
            ]
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp = float(f.readline())
        except FileNotFoundError:
            temp = 0
        return "Uptime: %s\nIdle: %.2f\nTemp: %3.3f\n" % (
            self.friendlyTime(uptime), idletime / (4 * uptime), temp / 1000,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    logging.info(statusGetter().status())
    logging.info(statusGetter().speedtest(True))
