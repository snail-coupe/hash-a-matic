import io
from pathlib import Path
from typing import List

import mastodon.Mastodon as MasApi
import yaml

from hashamatic.account import BotAccount, BotResult, iMessage, iPost

credsroot = Path.home() / ".hashBotNG" / "creds"

'''
access-token: <the access token for your account>
server: <the server url your account is on>
'''


class _Mastodon(BotAccount, iPost, iMessage):
    ''' A BotAccount for interacting with a Mastodon Account '''

    tags: List[str] = []
    client: MasApi

    def _setAccount(self, credspath: Path):
        with credspath.open() as f:
            creds = yaml.safe_load(f)
            self.client = MasApi(
                # client_id=creds["client-key"],
                # client_secret=creds["client-secret"],
                access_token=creds["access-token"],
                api_base_url=creds["server"]
            )
            self.creds = creds

    @staticmethod
    def text_and_tags(result: BotResult, limit: int = 500) -> str:
        text = result.text
        for tag in result.tags:
            tmp_text = f"{text} #{tag}"
            if len(tmp_text) <= limit:
                text = tmp_text
        return text

    def post(self, post: BotResult, direct: bool = False) -> bool:
        post.tags = self.tags + post.tags

        media_ids = None

        if post.image:
            imageIO = io.BytesIO()
            post.image.save(imageIO, format="PNG")
            imagedata = imageIO.getvalue()
            media_ids = self.client.media_post(imagedata, mime_type="image/png", description=post.alt_text)

        kwds = dict()

        if direct:
            kwds["visibility"] = "direct"

        if media_ids:
            kwds["media_ids"] = media_ids

        self.client.status_post(self.text_and_tags(post), **kwds)
        return True

    def message(self, user: str, message: BotResult) -> bool:
        message.text = f"@{user} {message.text}"
        return self.post(message, direct=True)


class Mastodon(_Mastodon):
    ''' default hashAmatic bot '''

    tags = ["hashAmatic"]

    def __init__(self):
        super().__init__()
        self._setAccount(credsroot / "crmbl.uk.yaml")
