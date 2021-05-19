from enum import Enum
from typing import Callable, List, Dict, Union, Optional, Any
import os
import logging
import discord
import math
from datetime import datetime, timedelta
import re
import dateutil.parser
from dateutil.relativedelta import relativedelta

# OTHER

COMMON_HELP_ARGS = [
    "@member/me - filter for one or more member",
    "#channel/here - filter for one or more channel",
    "<date1> - filter after <date1>",
    "<date2> - filter before <date2>",
    "fast - only read cache",
    "fresh - does not read cache (long)",
    "nsfw:allow/only - allow messages from nsfw channels",
    "mobile/mention - mentions users (fix @invalid-user bug)",
]


def generate_help(
    cmd: str,
    info: str,
    *,
    args=["all/everyone - include bots"],
    example="#mychannel1 @user",
    replace_args=[],
):
    arg_list = "* " + "\n* ".join(
        args + replace_args + COMMON_HELP_ARGS[len(replace_args) :]
    )
    return f"""```
%{cmd}: {info}
arguments:
{arg_list}
(Sample dates: 2020 / 2021-11 / 2021-06-28 / 2020-06-28T23:00 / today / week / 8days / 1y)
Example: %{cmd} {example}
```"""


def delta(t0: datetime):
    return round((datetime.now() - t0).total_seconds() * 1000)


def deltas(t0: datetime):
    return (datetime.now() - t0).total_seconds()


class FilterLevel(Enum):
    NONE = 0
    ALLOW = 1
    ONLY = 2


SPLIT_TOKEN = 1152317803


# DISCORD API


def debug(message: discord.Message, txt: str):
    logging.info(f"{message.guild} > #{message.channel}: {txt}")


async def code_message(message: discord.Message, content: str):
    await message.edit(content=f"```\n{content}\n```")


def mention(member_id: int) -> str:
    return f"<@{member_id}>"


def alt_mention(member_id: int) -> str:
    return f"<@!{member_id}>"


def role_mention(role_id: int) -> str:
    return f"<@&{role_id}>"


def channel_mention(channel_id: int) -> str:
    return f"<#{channel_id}>"


def message_link(message: discord.Message) -> str:
    return f"https://discord.com/channels/{message.channel.guild.id}/{message.channel.id}/{message.id}"


def escape_text(text: str) -> str:
    return discord.utils.escape_markdown(discord.utils.escape_mentions(text))


class FakeMessage:
    def __init__(self, id: int):
        self.id = id


def is_image_spoiler(message: discord.Message) -> bool:
    if len(message.attachments) > 0:
        return message.attachments[0].is_spoiler()
    elif len(message.embeds) > 0:
        return re.match(r"||[^|]*http[^|]||", message.content.lower()) is not None
    else:
        return False


def should_allow_spoiler(message: discord.Message, spoiler: FilterLevel) -> bool:
    is_spoiler = is_image_spoiler(message)
    return (
        not is_spoiler
        and spoiler <= FilterLevel.ALLOW
        or is_spoiler
        and spoiler >= FilterLevel.ALLOW
    )


# FILE


def is_extension(filepath: str, ext_list: List[str]) -> bool:
    filename, file_extension = os.path.splitext(filepath.lower())
    return file_extension in ext_list


def get_resource_path(filename: str) -> str:
    return os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", "resources", filename)
    )


# LISTS


def no_duplicate(seq: list) -> list:
    """
    Remove any duplicates on a list

    :param seq: original list
    :type seq: list
    :return: same list with no duplicates
    :rtype: list
    """
    return list(dict.fromkeys(seq))


# DICTS


def top_key(
    d: Dict[Union[str, int], int], key: Optional[Callable] = None
) -> Union[str, int]:
    if len(d) == 0:
        return None
    if key is None:
        key = lambda k: d[k]
    return sorted(d, key=key)[-1]


def val_sum(d: Dict[Any, int]) -> int:
    if len(d) == 0:
        return 0
    return sum(d.values())


def serialize(
    obj: Any, *, not_serialized: List[str] = [], dates: List[str] = []
) -> Dict:
    output = dict(obj.__dict__)
    for key in not_serialized:
        output.pop(key, None)
    for key in dates:
        if output[key]:
            try:
                output[key] = getattr(obj, key).isoformat()
            except AttributeError:
                pass
    return output


# MESSAGE FORMATTING


def aggregate(names: List[str]) -> str:
    """
    Aggregate names with , and &

    Example : "a, b, c & d"
    """
    if len(names) == 0:
        return ""
    elif len(names) == 1:
        return names[0]
    else:
        return ", ".join(names[:-1]) + " & " + names[-1]


def plural(count: int, word: str) -> str:
    return f"{count:,} {word}{'s' if count != 1 else ''}"


def percent(p: float) -> str:
    return f"{precise(100*p)}%"


def precise(p: float, *, precision: int = 2) -> str:
    if p == 0:
        return "0"
    precision = abs(min(0, math.ceil(math.log10(p)) - precision))
    s = "{:." + str(precision) + "f}"
    return s.format(p)


# DATE FORMATTING

ISO8601_REGEX = r"^([\+-]?\d{4}(?!\d{2}\b))((-?)((0[1-9]|1[0-2])(\3([12]\d|0[1-9]|3[01]))?|W([0-4]\d|5[0-2])(-?[1-7])?|(00[1-9]|0[1-9]\d|[12]\d{2}|3([0-5]\d|6[1-6])))([T\s]((([01]\d|2[0-3])((:?)[0-5]\d)?|24\:?00)([\.,]\d+(?!:))?)?(\17[0-5]\d([\.,]\d+)?)?([zZ]|([\+-])([01]\d|2[0-3]):?([0-5]\d)?)?)?)?$"
ISO8601_FULL = "0000-01-01T00:00:00"


def parse_iso_datetime(str_date: str) -> datetime:
    if re.match(
        "^\d{4}(-\d{2}(-\d{2}(T\d{2}(:\d{2}(:\d{2}(:\d{2})?)?)?)?)?)?$", str_date
    ):
        str_date = str_date + "0000-01-01T00:00:00"[len(str_date) :]
    return dateutil.parser.parse(str_date)


RELATIVE_REGEX = r"(yesterday|today|\d*hours?|\d+h(ours?)?|\d*days?|\d+d(ays?)?|\d*weeks?|\d+w(eeks?)?|\d*months?|\d+m(onths?)?|\d*years?|\d+y(ears?)?)"


def parse_relative_time(src: str) -> datetime:
    today = datetime.utcnow().date()
    today = datetime(today.year, today.month, today.day)
    if src == "today":
        return today
    elif src == "yesterday":
        return today - relativedelta(days=1)
    else:
        m = re.match("(\d*)(\w+)", src)
        delta = None
        value = int(m[1]) if m[1] else 1
        unit = m[2][0]
        if unit == "h":
            delta = relativedelta(hours=value)
        elif unit == "d":
            delta = relativedelta(days=value)
        elif unit == "w":
            delta = relativedelta(weeks=value)
        elif unit == "m":
            delta = relativedelta(months=value)
        elif unit == "y":
            delta = relativedelta(years=value)
        return datetime.utcnow() - delta


def parse_time(src: str) -> datetime:
    if re.match(RELATIVE_REGEX, src):
        return parse_relative_time(src)
    else:
        return parse_iso_datetime(src)


def str_date(date: datetime) -> str:
    return date.strftime("%d %b. %Y")  # 12 Jun. 2018


def str_datetime(date: datetime) -> str:
    return date.strftime("%H:%M, %d %b. %Y")  # 12:05, 12 Jun. 2018


def str_delta(delay: timedelta) -> str:
    seconds = delay.seconds
    minutes = seconds // 60
    hours = minutes // 60
    if delay.days < 1:
        if hours < 1:
            if minutes == 0:
                return "no time"
            elif minutes == 1:
                return "a minute"
            else:
                return f"{minutes} minutes"
        elif hours == 1:
            return "an hour"
        else:
            return f"{hours} hours"
    elif delay.days == 1:
        return "one day"
    else:
        return f"{delay.days:,} days"


def from_now(src: Optional[datetime]) -> str:
    if src is None:
        return "never"
    output = str_delta(datetime.utcnow() - src)
    if output == "no time":
        return "now"
    elif output == "one day":
        return "yesterday"
    return output + " ago"


# APP SPECIFIC


def get_intro(
    subject: str,
    full: bool,
    channels: List[discord.TextChannel],
    members: List[discord.Member],
    nmm: int,  # number of messages impacted
    nc: int,  # number of impacted channels
    start_datetime: datetime,
    stop_datetime: datetime,
) -> str:
    """
    Get the introduction sentence of the response
    """
    time_text = ""
    if start_datetime is not None:
        stop_datetime = datetime.now() if stop_datetime is None else stop_datetime
        time_text = f" (in {str_delta(stop_datetime - start_datetime)})"
    # Show all data (members, channels) when it's less than 5 units
    if len(members) == 0:
        # Full scan of the server
        if full:
            return f"{subject} in this server ({nc} channels, {nmm:,} messages){time_text}:"
        elif len(channels) < 5:
            return f"{aggregate([c.mention for c in channels])} {subject.lower()} in {nmm:,} messages{time_text}:"
        else:
            return f"These {len(channels)} channels {subject.lower()} in {nmm:,} messages{time_text}:"
    elif len(members) < 5:
        if full:
            return f"{aggregate([m.mention for m in members])} {subject.lower()} in {nmm:,} messages{time_text}:"
        elif len(channels) < 5:
            return (
                f"{aggregate([m.mention for m in members])} on {aggregate([c.mention for c in channels])} "
                f"{subject.lower()} in {nmm:,} messages{time_text}:"
            )
        else:
            return (
                f"{aggregate([m.mention for m in members])} on these {len(channels)} channels "
                f"{subject.lower()} in {nmm:,} messages{time_text}:"
            )
    else:
        if full:
            return f"These {len(members)} members {subject.lower()} in {nmm:,} messages{time_text}:"
        elif len(channels) < 5:
            return (
                f"These {len(members)} members on {aggregate([c.mention for c in channels])} "
                f"{subject.lower()} in {nmm:,} messages{time_text}:"
            )
        else:
            return (
                f"These {len(members)} members on these {len(channels)} channels "
                f"{subject.lower()} in {nmm:,} messages{time_text}:"
            )
