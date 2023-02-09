import argparse
import importlib
import logging
import sys

import cmd2
from cmd2.command_definition import with_default_category
from cmd2.decorators import with_argparser, with_category

from hashamatic.account import BotAccount, iMessage, iPost
from hashamatic.command import BotCmd

logger = logging.getLogger(__name__)


@with_default_category("Control")  # type: ignore
class BotShell(cmd2.Cmd):

    account: BotAccount = BotAccount.default()
    prompt: str = f"{account.__class__.__name__}> "

    acc_parser = argparse.ArgumentParser()
    acc_parser.add_argument("account", choices=BotAccount.get_choices())

    @with_argparser(acc_parser)  # type:  ignore
    def do_switch(self, args: argparse.Namespace):
        self.account = BotAccount.accounts[args.account]
        self.prompt = f"{self.account.__class__.__name__}> "
        self.enable_category("Posting")
        self.enable_category("Direct Messages")
        if not isinstance(self.account, iPost):
            self.disable_category("Posting", "This account handler doesn't support posting")
        if not isinstance(self.account, iMessage):
            self.disable_category("Direct Messages", "This account handler doesn't support direct messages")

    if BotAccount.post_choices():
        post_parser = argparse.ArgumentParser()
        BotCmd.build_subparsers(post_parser)

        @with_category("Posting")  # type: ignore
        @with_argparser(post_parser)  # type: ignore
        def do_post(self, args: argparse.Namespace):
            output = BotCmd.runner(args)
            self.account.post(output)

    if BotAccount.message_choices():
        dm_parser = argparse.ArgumentParser()
        dm_parser.add_argument("user", type=str)
        BotCmd.build_subparsers(dm_parser)

        @with_category("Direct Messages")  # type: ignore
        @with_argparser(dm_parser)  # type: ignore
        def do_dm(self, args: argparse.Namespace):
            output = BotCmd.runner(args)
            self.account.message(args.user, output)

    reload_parser = argparse.ArgumentParser()
    reload_parser.add_argument("module", choices=list(BotAccount.accounts.keys()) + list(BotCmd.commands.keys()))

    @with_argparser(reload_parser)  # type: ignore
    def do_reload(self, args: argparse.Namespace):
        module_name = None
        if args.module in BotAccount.accounts:
            logger.info("Reloading BotAccount Module: %s", args.module)
            module_name = BotAccount.accounts[args.module].__module__
        elif args.module in BotCmd.commands:
            logger.info("Reloading BotCmd Module: %s", args.module)
            module_name = BotCmd.commands[args.module].__module__

        if module_name:
            importlib.reload(sys.modules[module_name])
        else:
            raise ModuleNotFoundError(f"Can't reload {args.module}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("account", choices=BotAccount.get_choices(), nargs='?')

    parser_verbose = parser.add_mutually_exclusive_group()
    parser_verbose.add_argument("-q", "--quiet", action="store_true")
    parser_verbose.add_argument("-d", "--debug", action="store_true")

    args, remaining = parser.parse_known_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    shell = BotShell(allow_cli_args=False)

    if args.debug:
        shell.onecmd_plus_hooks("set debug True")

    if args.account:
        logging.info(f"switch {args.account}")
        shell.onecmd_plus_hooks(f"switch {args.account}")

    if remaining:
        logging.info(" ".join(remaining))
        shell.onecmd_plus_hooks(" ".join(remaining))
    else:
        shell.cmdloop()


if __name__ == "__main__":
    sys.exit(main())
