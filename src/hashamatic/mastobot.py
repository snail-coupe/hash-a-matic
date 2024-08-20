''' mastobot - stream mastodon bot '''

from contextlib import AbstractContextManager
from time import sleep
import logging
import argparse
import shlex

from bs4 import BeautifulSoup
from mastodon.streaming import StreamListener   # type: ignore

from hashamatic.account.mastodon import _Mastodon, Mastodon
from hashamatic.command import BotCmd, BotResult

logging.basicConfig(level=logging.DEBUG, force=True)


class BotArgParserError(Exception):
    ''' exception thrown by BotArgParser rather than exiting '''


class BotArgParser(argparse.ArgumentParser):
    ''' overloaded ArgumentParser that doesn't exit '''

    def error(self, message):
        raise BotArgParserError(message)

    def exit(self, status=0, message=None):
        if message:
            raise BotArgParserError(message)
        raise BotArgParserError(status)


class _MastoBot(_Mastodon, StreamListener, AbstractContextManager):
    ''' Streaming Mastodon Bot '''

    handle = None
    parser: BotArgParser | None = None

    def __enter__(self):
        self._build_parser()
        markers = self.client.markers_get("home")
        home_marker = markers['home']['last_read_id']
        # home_marker = 112760841988155689
        logging.info("playing catch up")
        logging.debug("> %d", home_marker)
        missed_conversations = self.client.conversations(since_id=home_marker)
        for convo in missed_conversations:
            self.on_conversation(convo)
        self.handle = self.client.stream_direct(self, run_async=True)
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        if self.handle:
            self.handle.close()

    def _build_parser(self):
        self.parser = BotArgParser("*", exit_on_error=False)
        self.parser.add_argument("--post", "-p", action="store_true")
        BotCmd.build_subparsers(self.parser)

    def on_conversation(self, conversation):
        self.client.markers_set(
            "home",
            conversation.last_status.id
        )
        if conversation.last_status.account.username in ["snail"]:
            soup = BeautifulSoup(
                conversation.last_status.content,
                features="lxml"
            )
            print(soup.text)
            if self.parser and "*" in soup.text:
                cmdline = soup.text.split("*", maxsplit=1)[1]
                try:
                    args = self.parser.parse_args(shlex.split(cmdline))
                    output = BotCmd.runner(args)
                    kwds = {}
                    if not args.post:
                        kwds["direct"] = conversation.last_status.account.username
                        kwds["in_reply_to"] = conversation.last_status.id
                    self.post(
                        output, **kwds
                    )
                except BotArgParserError as e:
                    output = BotResult(text=self.parser.format_usage() + str(e))
                    self.post(
                        output,
                        direct=conversation.last_status.account.username,
                        in_reply_to=conversation.last_status.id,
                    )
        else:
            logging.info("Bad User %s", conversation.last_status.account.username)

        return super().on_conversation(conversation)


class MastoBot(_MastoBot, Mastodon):
    ''' streaming hashamatic '''


with MastoBot() as bot:
    sleep(5)
    while bot.handle.is_receiving():
        # logging.debug("Core Loop sleeping")
        sleep(5)
