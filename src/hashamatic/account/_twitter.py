import io
import json
import logging
from pathlib import Path

import twitter
import yaml

from hashamatic.account import BotAccount, BotResult, iMessage, iPost

logger = logging.getLogger()

credsroot = Path.home() / ".hashBotNG" / "creds"


class Twitter(BotAccount, iPost, iMessage):

    def __init__(self):
        with open(credsroot / "twitter.yaml") as f:
            creds = yaml.safe_load(f)
            oauth = twitter.OAuth(
                token=creds["token"],
                token_secret=creds["token_secret"],
                consumer_key=creds["consumer_key"],
                consumer_secret=creds["consumer_secret"],
            )
            bearer = twitter.OAuth2(
                consumer_key=creds["consumer_key"],
                consumer_secret=creds["consumer_secret"],
                bearer_token=creds["bearer"]
            )
            self.userApi = twitter.Twitter(
                auth=oauth,
                retry=True,
            )
            self.appApi = twitter.Twitter(
                auth=bearer,
                retry=True,
            )
            self.appApi2 = twitter.Twitter(
                auth=bearer,
                retry=True,
                api_version='2', format="",
            )

            self.uploadApi = twitter.Twitter(
                domain='upload.twitter.com',
                auth=oauth,
                retry=True,
            )
            self._rootUserIds = creds["rootUsers"]
            self._creds = creds

    @staticmethod
    def text_and_tags(result: BotResult, limit: int = 160) -> str:
        text = result.text
        for tag in result.tags:
            tmp_text = f"{text} #{tag}"
            if len(tmp_text) <= limit:
                text = tmp_text
        return text

    def post(self, post: BotResult) -> bool:
        media_ids = None

        if post.image:
            imageIO = io.BytesIO()
            post.image.save(imageIO, format="PNG")
            imagedata = imageIO.getvalue()
            media_ids = self.uploadApi.media.upload(media=imagedata)["media_id_string"]

        kwds = dict()
        # if inReplyTo:
        #     kwds["in_reply_to_status_id"] = "%s"%inReplyTo
        if media_ids:
            kwds["media_ids"] = media_ids

        self.userApi.statuses.update(status=self.text_and_tags(post), **kwds)
        return True

    def message(self, user: str, message: BotResult) -> bool:
        user_id = self.lookupUserId(user)
        eventObj = {
            "type": "message_create",
            "message_create": {
                "target": {
                    "recipient_id": user_id
                },
                "message_data": {
                    "text": message.text
                }
            }
        }

        if message.image:
            imageIO = io.BytesIO()
            message.image.save(imageIO, format="PNG")
            imagedata = imageIO.getvalue()
            media_id = self.uploadApi.media.upload(media=imagedata)["media_id_string"]

            eventObj['message_create']['message_data']['attachment'] = {  # type: ignore
                'type': "media",
                'media': {'id': media_id}
            }

        self.userApi.direct_messages.events.new(
            _json={"event": eventObj},
            _method="POST",
        )

        return True

    def lookupUserId(self, userName: str) -> str:
        resp = json.loads(self.appApi2.users.by.username._userName(
            _userName=userName,
        ))
        return resp["data"]["id"]

    def lookupUserName(self, userId: str) -> str:
        resp = json.loads(self.appApi2.users._userId(
            _userId=userId,
        ))
        return resp["data"]["username"]

    def isRootUser(self, userId: str) -> bool:
        return str(userId) in self._rootUserIds
