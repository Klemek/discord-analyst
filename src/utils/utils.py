from typing import List
import os
import logging
import discord

# DISCORD API


def debug(message: discord.Message, txt: str):
    logging.info(f"{message.guild} > #{message.channel}: {txt}")


async def code_message(message: discord.Message, content: str):
    await message.edit(content=f"```\n{content}\n```")


def mention(member_id: int) -> str:
    return f"<@{member_id}>"


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
    return str(count) + " " + word + ("s" if count != 1 else "")


def day_interval(interval: int) -> str:
    if interval == 0:
        return "today"
    elif interval == 1:
        return "yesterday"
    else:
        return f"{interval} days ago"


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
            return f"{aggregate([c.mention for c in channels])} {subject} in {nmm:,} messages:"
        else:
            return f"These {len(channels)} channels {subject} in {nmm:,} messages:"
    elif len(members) < 5:
        if full:
            return f"{aggregate([m.mention for m in members])} {subject} in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"{aggregate([m.mention for m in members])} on {aggregate([c.mention for c in channels])} "
                f"{subject} in {nmm:,} messages:"
            )
        else:
            return (
                f"{aggregate([m.mention for m in members])} on these {len(channels)} channels "
                f"{subject} in {nmm:,} messages:"
            )
    else:
        if full:
            return f"These {len(members)} members {subject} in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"These {len(members)} members on {aggregate([c.mention for c in channels])} "
                f"{subject} in {nmm:,} messages:"
            )
        else:
            return (
                f"These {len(members)} members on these {len(channels)} channels "
                f"{subject} in {nmm:,} messages:"
            )
