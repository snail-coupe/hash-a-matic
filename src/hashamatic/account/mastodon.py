''' Mastodon Accounts for hashamatic '''

import io
from pathlib import Path
from typing import List, Optional, Dict, Any

import mastodon
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
    client: mastodon.Mastodon
    creds: Any

    def _set_account(self, credspath: Path):
        with credspath.open() as f:
            creds = yaml.safe_load(f)
            self.client = mastodon.Mastodon(
                # client_id=creds["client-key"],
                # client_secret=creds["client-secret"],
                access_token=creds["access-token"],
                api_base_url=creds["server"]
            )
            self.creds = creds

    @staticmethod
    def text_and_tags(
        result: BotResult,
        direct: Optional[str] = None,
        limit: int = 500
    ) -> str:
        ''' apply tags to end of text upto given char limit '''
        if direct:
            text = f"@{direct} {result.text}"
        else:
            text = result.text
        for tag in result.tags:
            tmp_text = f"{text} #{tag}"
            if len(tmp_text) <= limit:
                text = tmp_text
        return text

    def find_latest_convo_with(self, user: str) -> Optional[int]:
        ''' attempt to find id of latest conversation with given user '''
        try:
            user_dict = self.client.account_lookup(user)
        except Mastodon.client.MastodonNotFoundError:
            return None
        target_id = user_dict.id

        convos = self.client.conversations()
        while convos:
            for convo in convos:
                if len(convo.accounts) == 1:
                    conv_user = convo.accounts[0]
                    if target_id == conv_user.id:
                        return convo.last_status.id
            convos = self.client.fetch_previous(convos)

        return None

    def post(
        self,
        post: BotResult,
        direct: Optional[str] = None,
        public: bool = True,
        in_reply_to: Optional[str] = None
    ) -> bool:
        post.tags = self.tags + post.tags

        node: Optional[BotResult] = post
        while node:
            self.logger.info("Post (%s)", in_reply_to)

            media_ids = None

            if node.image:
                image_io = io.BytesIO()
                node.image.save(image_io, format="PNG")
                imagedata = image_io.getvalue()
                media_ids = self.client.media_post(
                    imagedata,
                    mime_type="image/png",
                    description=node.alt_text
                )

            kwds: Dict[str, Any] = dict()

            if direct:
                kwds["visibility"] = "direct"
                kwds["in_reply_to_id"] = self.find_latest_convo_with(direct)
            elif not public:
                kwds["visibility"] = "unlisted"

            if in_reply_to:
                kwds["in_reply_to_id"] = in_reply_to

            if media_ids:
                kwds["media_ids"] = media_ids

            if node.warning:
                kwds["spoiler_text"] = node.warning

            result = self.client.status_post(
                self.text_and_tags(node, direct), **kwds
            )
            in_reply_to = result['id']
            node = node.next

        return True

    def message(self, user: str, message: BotResult) -> bool:
        return self.post(message, direct=user)


class Mastodon(_Mastodon):
    ''' default hashAmatic bot '''

    tags = ["hashAmatic"]

    def __init__(self):
        super().__init__()
        self._set_account(credsroot / "crmbl.uk.yaml")


class Griddle(_Mastodon):
    ''' Griddle bot '''

    tags = ["Griddle"]

    def __init__(self):
        super().__init__()
        self._set_account(credsroot / "griddle.yaml")
