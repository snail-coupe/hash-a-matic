''' Tumblr Accounts for hashamatic '''

import io
import os
import tempfile
from pathlib import Path
from typing import List, Optional

import pytumblr2  # type: ignore
import yaml
from PIL.Image import Image

from hashamatic.account import BotAccount, BotResult, iPost

credsroot = Path.home() / ".hashBotNG" / "creds"

# consumer_key: <key>
# consumer_secret: <secret>
# oauth_key: <key>
# oauth_secret: <secret>


class Tumblr(BotAccount, iPost):
    ''' A Tumblr BotAccount '''

    def __init__(self):
        with open(credsroot / "tumblr.yaml", encoding="ascii") as f:
            creds = yaml.safe_load(f)
            self.npf_client = pytumblr2.TumblrRestClient(
                creds['consumer_key'], creds['consumer_secret'],
                creds['oauth_key'], creds['oauth_secret']
            )

            self._creds = creds
            self.state = "published"
            self.format = "html"
        super().__init__()

    def post_npf(self, post: BotResult):
        ''' post in tumblr's NPF '''
        content = []
        media: Optional[dict] = None
        (tfhandle, tfname) = tempfile.mkstemp()

        if post.image:
            image_io = io.BytesIO()
            post.image.save(image_io, format="PNG")
            imagedata = image_io.getvalue()
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

    def post_plaintext(self, text: str, tags: List[str]):
        ''' post plaintext '''
        self.npf_client.legacy_create_text(
            'hashamatic.tumblr.com',
            state=self.state,
            format=self.format,
            body=text,
            tags=list(tags)
        )

    def post_image(self, raw_image: Image, caption: str, tags: List[str]):
        ''' post an image in old format '''
        (tfhandle, tfname) = tempfile.mkstemp()
        image_io = io.BytesIO()
        raw_image.save(image_io, format="PNG")
        imagedata = image_io.getvalue()
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

        return self.post_npf(post)
