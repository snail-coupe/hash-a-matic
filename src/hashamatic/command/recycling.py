import logging
from argparse import ArgumentParser

try:
    from argparse import Namespace

    from ukbinday import BinDayGetter

    from hashamatic.command import BotCmd, BotResult

    class Rubbish(BotCmd):
        ''' Bin Collection Infomation for a subset of UK Boroughs. '''
        @staticmethod
        def add_argparse_arguments(parser: ArgumentParser) -> ArgumentParser:
            parser.add_argument("number", nargs='?', type=str, default=None)
            parser.add_argument("postcode", nargs=2)
            return parser

        def run(self, args: Namespace) -> BotResult:
            postCode = (" ".join(args.postcode)).upper()
            return BotResult(text=BinDayGetter(
                postcode=postCode, housenumber=args.number
            ).bin_day())
except ImportError:
    logging.debug("failed to import BotCmd interface")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("number", nargs='?', type=str, default=None)
    parser.add_argument("postcode", nargs=2)
    args = parser.parse_args()
    postCode = (" ".join(args.postcode)).upper()

    logging.basicConfig(level=logging.INFO, force=True)
    logging.info("Lookup from Scratch:")
    logging.info(BinDayGetter(housenumber=args.number, postcode=postCode).bin_day())
