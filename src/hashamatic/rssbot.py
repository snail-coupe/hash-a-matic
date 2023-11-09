''' rssbot - gets and posts latest items from RSS feeds '''

import argparse
import logging
import logging.handlers
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests
import yaml
from bs4 import BeautifulSoup
from tendo.singleton import SingleInstance, SingleInstanceException

from hashamatic.account.mastodon import BotResult, _Mastodon

credsroot = Path.home() / ".hashBotNG" / "creds"
config_file = Path.home() / ".hashBotNG" / "configs" / "rssbot.yaml"
cache_path = Path.home() / ".hashBotNG" / "cache"
log_path = Path.home() / ".hashBotNG" / "rss.log"

if not cache_path.exists():
    cache_path.mkdir(parents=True, exist_ok=True)

with config_file.open("r") as config_io:
    config = yaml.load(config_io, yaml.SafeLoader)

bots = config.keys()


def parse_item_time(s: str) -> datetime:
    ''' trial string to time conversion based upon
        observed formats '''
    try:
        return datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        pass
    try:
        return datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        pass
    raise ValueError(f"Failed to parse: {s}")


class RSSBot(_Mastodon):
    ''' Mastobot specialised for RSS Feeds '''
    def __init__(self, bot: Optional[str] = None) -> None:
        super().__init__()
        if bot:
            self.bot = bot
            self._set_account(
                credsroot / f"{config[self.bot]['account']}.yaml"
            )
            self.url = config[self.bot]["url"]

    @staticmethod
    def get_ttl(soup) -> Union[timedelta, None]:
        ''' attempt to determine TTL for feed as timedelta '''
        ttl = soup.select("rss channel ttl")
        if ttl:
            return timedelta(minutes=int(ttl[0].text))
        return None

    def run(self, dryrun: bool = False):
        ''' run the process '''
        try:
            guid_path = cache_path / f"{self.bot}_guids.yaml"
            xml_path = cache_path / f"{self.url.split('//')[1]}"
            if not xml_path.parent.exists():
                xml_path.parent.mkdir(parents=True)
            oguids: Dict[str, Any]
            if guid_path.exists():
                with guid_path.open("r") as guid_io:
                    oguids = yaml.load(guid_io, yaml.SafeLoader)
            else:
                oguids = {}
            soup = None
            if xml_path.exists():
                logging.debug("Trying Cached Feed")
                soup = BeautifulSoup(xml_path.read_bytes(), features="xml")
                ttl = self.get_ttl(soup)
                if ttl:
                    expire_time = ttl + datetime.fromtimestamp(
                        xml_path.stat().st_mtime
                    )
                    if expire_time < datetime.now():
                        logging.debug("Feed Stale")
                        soup = None
                else:
                    logging.debug("Feed has no TTL")
                    soup = None
                if soup:
                    logging.debug("Feed cache in date, no need to do anything")
                    return
            logging.debug("Requesting: %s", config[self.bot]["url"])
            rss_request = requests.get(self.url, timeout=15)
            soup = BeautifulSoup(rss_request.content, features="xml")
            xml_path.write_bytes(rss_request.content)
            nguids: Dict[str, Any] = {}
            items = soup.find_all("item")
            for item in sorted(
                items,
                key=lambda x: parse_item_time(x.pubDate.text)
            ):
                itime = parse_item_time(item.pubDate.text)
                nguids[item.guid.text] = [item.pubDate.text, item.title.text]
                if itime.timestamp() < (
                    datetime.now().timestamp()
                    - timedelta(hours=24).total_seconds()
                ):
                    # never (re-)publish anything published/updated
                    # more than a day ago
                    continue
                logging.debug(
                    "%s: %s : %s",
                    item.guid.text, str(itime), item.title.text
                )
                if item.guid.text not in oguids:
                    url = item.link.text.split("?")[0]
                    toot = BotResult(
                        text=f"{item.title.text}\n\n{url} ({itime.strftime('%c %Z')})\n\n{item.description.text}\n\n",
                        tags=["News", "📰"] + config[self.bot]["tags"]
                    )
                    if not dryrun:
                        logging.debug("%s", str(toot))
                        self.post(toot, public=False)
                    else:
                        logging.info("TOOT: %s", str(toot))

            # remove anything published/updated more than a week ago from cache
            weekold = datetime.now().timestamp() - timedelta(days=7).total_seconds()
            guids: Dict[str, Any] = dict(filter(
                lambda x: parse_item_time(x[1][0]).timestamp() < weekold,
                oguids.items()
            ))
            # now merge in everything in currently feed
            guids.update(nguids)
            if not dryrun:
                guid_path.write_text(yaml.dump(guids, Dumper=yaml.SafeDumper))
            else:
                logging.debug("%s", yaml.dump(guids, Dumper=yaml.SafeDumper))

        except Exception as exc:
            logging.debug(exc)
            raise


def main():
    ''' main () '''
    parser = argparse.ArgumentParser()
    parser.add_argument("bot", choices=bots, help="Bot to run", nargs='?')
    parser.add_argument("--debug", "-d", action="store_true")
    parser.add_argument("--dryrun", "-n", action="store_true")
    args = parser.parse_args()

    if args.debug:
        loglvl = logging.DEBUG
    else:
        loglvl = logging.INFO

    consolehndlr = logging.StreamHandler()
    consolehndlr.setLevel(logging.DEBUG)
    logfilehndlr = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=16384,
        backupCount=5,
    )
    logfilehndlr.setLevel(logging.INFO)

    logging.basicConfig(
        level=loglvl, force=True,
        handlers=[logfilehndlr, consolehndlr]
    )

    if args.bot:
        bots_to_run = [args.bot]
    else:
        bots_to_run = list(filter(lambda x: "default" in config[x] and config[x]["default"], bots))

    logging.debug(bots_to_run)

    try:
        _ = SingleInstance(lockfile=f"{config_file}.lock")
        for bot in bots_to_run:
            logging.debug("Running: %s", bot)
            botodon = RSSBot(bot)
            botodon.run(args.dryrun)
    except SingleInstanceException:
        logging.info("Cannot get Lock, is another instance running?")


if __name__ == "__main__":
    main()
