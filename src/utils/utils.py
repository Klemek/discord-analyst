from typing import List, Dict, Union, Optional, Any
import os
import logging
import discord
import math
from datetime import datetime

# OTHER

COMMON_HELP_ARGS = [
    "@member/me - filter for one or more member",
    "#channel/here - filter for one or more channel",
    "fast - only read cache",
    "fresh - does not read cache (long)",
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
        replace_args + COMMON_HELP_ARGS[len(replace_args) :] + args
    )
    return f"""```
%{cmd}: {info}
arguments:
{arg_list}
Example: %{cmd} {example}
```"""


def delta(t0: datetime):
    return round((datetime.now() - t0).total_seconds() * 1000)


def deltas(t0: datetime):
    return (datetime.now() - t0).total_seconds()


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


class FakeMessage:
    def __init__(self, id: int):
        self.id = id


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


def top_key(d: Dict[Union[str, int], int]) -> Union[str, int]:
    return sorted(d, key=lambda k: d[k])[-1]


def val_sum(d: Dict[Any, int]) -> int:
    return sum(d.values())


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


def str_date(date: datetime) -> str:
    return date.strftime("%d %b. %Y")  # 12 Jun. 2018


def str_datetime(date: datetime) -> str:
    return date.strftime("%H:%M, %d %b. %Y")  # 12:05, 12 Jun. 2018


def from_now(src: Optional[datetime]) -> str:
    if src is None:
        return "never"
    delay = datetime.utcnow() - src
    seconds = delay.seconds
    minutes = seconds // 60
    hours = minutes // 60
    if delay.days < 1:
        if hours < 1:
            if minutes == 0:
                return "now"
            elif minutes == 1:
                return "a minute ago"
            else:
                return f"{minutes} minutes ago"
        elif hours == 1:
            return "an hour ago"
        else:
            return f"{hours} hours ago"
    elif delay.days == 1:
        return "yesterday"
    else:
        return f"{delay.days:,} days ago"


# APP SPECIFIC


def get_intro(
    subject: str,
    full: bool,
    channels: List[discord.TextChannel],
    members: List[discord.Member],
    nmm: int,  # number of messages impacted
    nc: int,  # number of impacted channels
) -> str:
    """
    Get the introduction sentence of the response
    """
    # Show all data (members, channels) when it's less than 5 units
    if len(members) == 0:
        # Full scan of the server
        if full:
            return f"{subject} in this server ({nc} channels, {nmm:,} messages):"
        elif len(channels) < 5:
            return f"{aggregate([c.mention for c in channels])} {subject.lower()} in {nmm:,} messages:"
        else:
            return (
                f"These {len(channels)} channels {subject.lower()} in {nmm:,} messages:"
            )
    elif len(members) < 5:
        if full:
            return f"{aggregate([m.mention for m in members])} {subject.lower()} in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"{aggregate([m.mention for m in members])} on {aggregate([c.mention for c in channels])} "
                f"{subject.lower()} in {nmm:,} messages:"
            )
        else:
            return (
                f"{aggregate([m.mention for m in members])} on these {len(channels)} channels "
                f"{subject.lower()} in {nmm:,} messages:"
            )
    else:
        if full:
            return (
                f"These {len(members)} members {subject.lower()} in {nmm:,} messages:"
            )
        elif len(channels) < 5:
            return (
                f"These {len(members)} members on {aggregate([c.mention for c in channels])} "
                f"{subject.lower()} in {nmm:,} messages:"
            )
        else:
            return (
                f"These {len(members)} members on these {len(channels)} channels "
                f"{subject.lower()} in {nmm:,} messages:"
            )
