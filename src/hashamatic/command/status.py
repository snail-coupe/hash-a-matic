''' various status botCmds '''

import hashlib
import io
import logging
import os
from typing import Tuple, Optional

import requests
import PIL.Image
from speedtest import Speedtest

try:
    from argparse import ArgumentParser, Namespace

    from hashamatic.command import BotCmd, BotResult

    class Hash(BotCmd):
        ''' Guess the hash '''
        def run(self, _args: Namespace) -> BotResult:
            r = os.urandom(128)
            m = hashlib.md5()
            m.update(r)
            return BotResult(
                text=m.digest().hex(),
                tags=["hash"]
            )

    class Status(BotCmd):
        ''' Basic status information about the server housing the bot. '''
        def run(self, _args: Namespace) -> BotResult:
            return BotResult(text=StatusGetter().status())

    class SpeedTest(BotCmd):
        ''' Perform a speedtest of the server housing the bot. '''
        def run(self, args: Namespace) -> BotResult:
            (text, image) = StatusGetter().speedtest(args.graphical)
            return BotResult(image=image, text=text)

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("--graphical", "-g", action="store_true")
            return parser

except ImportError:
    logging.debug("failed to import BotCmd interface")


class StatusGetter():
    ''' class to return various status info '''
    def __init__(self):
        pass

    def friendly_time(self, t: float) -> str:
        ''' convert float based timedelta into something more friendly '''
        t = int(t)
        sec = int(t % 60)
        t = t / 60
        mm = int(t % 60)
        t = t / 60
        hr = int(t % 24)
        t = t / 24
        return f"{int(t)}d{hr:02d}:{mm:02d}:{sec:02d}"

    def speedtest(self, share=False) -> Tuple[str, Optional[PIL.Image.Image]]:
        ''' performs a speedtest of the internet connection '''
        s = Speedtest()
        url = None

        upload = s.upload() / 1000 / 1000
        download = s.download() / 1000 / 1000
        ping = s.results.ping
        if share:
            url = s.results.share()
            data = requests.get(url, timeout=20)
            image = PIL.Image.open(io.BytesIO(data.content))
        else:
            image = None

        return "Ping: %3.2f\nUpld: %3.2f\nDnld: %3.2f\n" % (
            ping, upload, download,
        ), image

    def status(self) -> str:
        ''' return uptime, idle and temp '''
        with open('/proc/uptime', "r", encoding="ascii") as f:
            (uptime, idletime) = [
                float(i) for i in f.readline().split(" ")
            ]
        try:
            with open(
                "/sys/class/thermal/thermal_zone0/temp",
                encoding="ascii"
            ) as f:
                temp = float(f.readline())
        except FileNotFoundError:
            temp = 0
        return "Uptime: %s\nIdle: %.2f\nTemp: %3.3f\n" % (
            self.friendly_time(uptime), idletime / (4 * uptime), temp / 1000,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    logging.info(StatusGetter().status())
    logging.info(StatusGetter().speedtest(True))
