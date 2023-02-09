import io
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import pytumblr2
import yaml
from PIL.Image import Image

from hashamatic.account import BotAccount, BotResult, iPost

credsroot = Path.home() / ".hashBotNG" / "creds"

'''
consumer_key: <key>
consumer_secret: <secret>
oauth_key: <key>
oauth_secret: <secret>
'''


class Tumblr(BotAccount, iPost):
    ''' A Tumblr BotAccount '''

    def __init__(self):
        with open(credsroot / "tumblr.yaml") as f:
            creds = yaml.safe_load(f)
            self.npf_client = pytumblr2.TumblrRestClient(
                creds['consumer_key'], creds['consumer_secret'],
                creds['oauth_key'], creds['oauth_secret']
            )

            self._creds = creds
            self.state = "published"
            self.format = "html"

    def postNpf(self, post: BotResult):
        content = []
        media: Optional[dict] = None
        (tfhandle, tfname) = tempfile.mkstemp()

        if post.image:
            imageIO = io.BytesIO()
            post.image.save(imageIO, format="PNG")
            imagedata = imageIO.getvalue()
            tfio = os.fdopen(tfhandle, "wb")
            tfio.write(imagedata)
            tfio.close()

            imgblk = {
                "type": "image",
                "media": [{
                    "type": "image/png",
                    "identifier": "upload_media",
                }]
            }
            if post.alt_text:
                imgblk["alt_text"] = post.alt_text
            content.append(imgblk)
            media = {
                "upload_media": tfname
            }
        if post.text:
            content.append({
                "type": "text",
                "text": post.text
            })
        if content:
            postkwds = dict(
                blogname='hashamatic.tumblr.com',
                state=self.state,
                content=content,
                tags=list(post.tags),
            )
            if media:
                postkwds["media_sources"] = media

            self.npf_client.create_post(**postkwds)
        if os.path.exists(tfname):
            os.unlink(tfname)

    def postText(self, text: str, tags: List[str]):
        self.npf_client.legacy_create_text(
            'hashamatic.tumblr.com',
            state=self.state,
            format=self.format,
            body=text,
            tags=list(tags)
        )

    def postImage(self, imageRaw: Image, caption: str, tags: List[str]):
        (tfhandle, tfname) = tempfile.mkstemp()
        imageIO = io.BytesIO()
        imageRaw.save(imageIO, format="PNG")
        imagedata = imageIO.getvalue()
        tfio = os.fdopen(tfhandle, "wb")
        tfio.write(imagedata)
        tfio.close()
        ret = self.npf_client.legacy_create_photo(
            'hashamatic.tumblr.com',
            state=self.state,
            format=self.format,
            caption=caption,
            data=tfname,
            tags=sorted(tags)
        )
        os.unlink(tfname)
        return ret

    def post(self, post: BotResult) -> bool:
        post.tags = ["hashAmatic"] + post.tags

        return self.postNpf(post)
