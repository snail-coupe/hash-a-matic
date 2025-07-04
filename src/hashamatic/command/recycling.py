"""botcmd to return bin collection info"""

import logging
from argparse import ArgumentParser

try:
    from argparse import Namespace

    from ukbinday import BinDayGetter  # type: ignore

    from hashamatic.command import BotCmd, BotResult

    class Rubbish(BotCmd):
        """Bin Collection Infomation for a subset of UK Boroughs."""

        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("number", nargs="?", type=str, default=None)
            parser.add_argument("postcode", nargs=2)
            return parser

        def run(self, args: Namespace) -> BotResult:
            postcode = (" ".join(args.postcode)).upper()
            days = BinDayGetter(postcode=postcode, housenumber=args.number).bin_day()
            return BotResult(text=f"{days}")
except ImportError:
    logging.debug("failed to import BotCmd interface")


if __name__ == "__main__":
    from ukbinday import BinDayGetter  # type: ignore

    cliparser = ArgumentParser()
    cliparser.add_argument("number", nargs="?", type=str, default=None)
    cliparser.add_argument("postcode", nargs=2)
    cliargs = cliparser.parse_args()

    logging.basicConfig(level=logging.INFO, force=True)
    logging.info("Lookup from Scratch:")
    logging.info(
        BinDayGetter(
            housenumber=cliargs.number, postcode=(" ".join(cliargs.postcode)).upper()
        ).bin_day()
    )
