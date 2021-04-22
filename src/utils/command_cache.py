from typing import List
import logging
import discord

from scanners import Scanner

command_cache = {}


def cache(scanner: Scanner, message: discord.Message, args: List[str]):
    id = message.channel.id
    command_cache[id] = (
        type(scanner),
        list(args),
        [str(channel.id) for channel in message.channel_mentions]
        + [str(member.id) for member in message.mentions],
    )


async def repeat(
    client: discord.client,
    message: discord.Message,
    *args: str,
    add_args: List[str] = [],
):
    if len(args) > 1 and args[1] == "help":
        await client.bot.help(client, message, "help", args[0])
        return
    id = message.channel.id
    if id not in command_cache:
        await message.channel.send(
            "No command to repeat on this channel (type %help for more info)",
            reference=message,
        )
        return
    (
        scannerType,
        original_args,
        original_mentions,
    ) = command_cache[id]
    args = original_args + add_args + list(args[1:]) + ["fast"]
    logging.info(f"repeating {args}")
    await scannerType().compute(
        client, message, *args, other_mentions=original_mentions
    )
