from typing import List
import logging
import discord

# DISCORD API


def debug(message: discord.Message, txt: str):
    logging.info(f"{message.guild} > #{message.channel}: {txt}")


async def code_message(message: discord.Message, content: str):
    await message.edit(content=f"```\n{content}\n```")


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
