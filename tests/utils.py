from typing import List, Optional, Dict, Union
from unittest import TestCase
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import random
import string


class AsyncTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    def _await(self, fn):
        return self.loop.run_until_complete(fn)


RANDOM_TEXT_CHARS = string.ascii_letters + string.digits + string.punctuation


def random_text(min_len: int = 3, max_len: int = 45):
    return "".join(
        random.choice(RANDOM_TEXT_CHARS)
        for _ in range(random.randrange(min_len, max_len))
    )


def fake_guild(id: int = 1):
    return MagicMock(id=id)


def fake_channel(id: int = 1, name: str = "fake-channel"):
    return MagicMock(id=id, name=name, guild=fake_guild())


def fake_message(
    id: int = 1,
    channel_id: int = 1,
    channel_name: str = "fake-channel",
    created_at: Optional[Union[datetime, timedelta]] = None,
    edited_at: Optional[datetime] = None,
    author: int = 1,
    pinned: bool = False,
    mention_everyone: bool = False,
    tts: bool = False,
    bot: bool = False,
    content: Optional[str] = None,
    mentions: Optional[List[int]] = None,
    reference: Optional[int] = None,
    role_mentions: Optional[List[int]] = None,
    channel_mentions: Optional[List[int]] = None,
    image: bool = False,
    attachment: bool = False,
    embed: bool = False,
    reactions: Optional[Dict[str, List[int]]] = None,
):
    if created_at is None:
        created_at = datetime.now() + timedelta(hours=random.randrange(-30 * 24, 0))
    elif isinstance(created_at, timedelta):
        created_at = datetime.now() + created_at
    if isinstance(edited_at, timedelta):
        edited_at = datetime.now() + edited_at
    if content is None:
        content = random_text()
    if mentions is None:
        mentions = []
    if role_mentions is None:
        role_mentions = []
    if channel_mentions is None:
        channel_mentions = []
    if reactions is None:
        reactions = {}
    return MagicMock(
        id=id,
        channel=fake_channel(channel_id, channel_name),
        created_at=created_at,
        edited_at=edited_at,
        author=author,
        pinned=pinned,
        mention_everyone=mention_everyone,
        tts=tts,
        bot=bot,
        content=content,
        mentions=mentions,
        raw_mentions=mentions,
        reference=reference,
        role_mentions=role_mentions,
        raw_role_mentions=role_mentions,
        channel_mentions=channel_mentions,
        raw_channel_mentions=channel_mentions,
        image=image,
        attachment=attachment,
        embed=embed,
        reactions=reactions,
    )
