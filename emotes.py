from datetime import datetime
import discord
import re


def debug(message, txt):
    print(f"{message.guild} > #{message.channel}: {txt}")


# CLASSES

class Emote:
    def __init__(self, emoji):
        self.emoji = emoji
        self.name = str(emoji)
        self.usages = 0
        self.reactions = 0
        self.last_used = None

    def used(self):
        return self.usages > 0 or self.reactions > 0

    def score(self):
        return self.usages + self.reactions + 1 / (100000 * (self.use_days() + 1))

    def life_days(self):
        return (datetime.today() - self.emoji.created_at).days

    def use_days(self):
        if self.last_used is None:
            return self.life_days()
        else:
            return (datetime.today() - self.last_used).days


# ANALYSIS


async def analyse_channel(client, channel, emotes, member, progress, delta, nc):
    nm = 0
    try:
        async for m in channel.history(limit=None):
            if member is None and m.author != client.user or m.author == member:
                found = [name for name in re.findall(r"(<:\w+:\d+>)", m.content) if name in emotes]
                for name in found:
                    emotes[name].usages += 1
                    if emotes[name].last_used is None:
                        emotes[name].last_used = m.created_at
                if member is None:
                    for reaction in m.reactions:
                        name = str(reaction.emoji)
                        if not (isinstance(reaction.emoji, str)) and name in emotes:
                            emotes[name].reactions += reaction.count
                            if emotes[name].last_used is None:
                                emotes[name].last_used = m.created_at
                nm += 1
                if (delta + nm) % 1000 == 0:
                    await progress.edit(content=f"```{(delta + nm) // 1000}k messages and {nc} channels analysed```")
        return nm
    except discord.errors.Forbidden:
        return -1


# RESULTS


def get_place(n):
    if n == 0:
        return ":first_place:"
    if n == 1:
        return ":second_place:"
    if n == 2:
        return ":third_place:"
    return f"**#{n + 1}**"


def get_usage(emote):
    if emote.usages == 0 and emote.reactions == 0:
        return "never used "
    elif emote.usages == 1:
        return "1 time "
    else:
        return f"{emote.usages} times "


def get_reactions(emote):
    if emote.reactions == 0:
        return ""
    elif emote.reactions == 1:
        return "and 1 reaction "
    else:
        return f"and {emote.reactions} reactions "


def get_life(emote, show_life):
    if not show_life:
        return ""
    else:
        return f"(in {emote.life_days()} days) "


def get_last_used(emote):
    if emote.usages == 0 and emote.reactions == 0:
        return ""
    elif emote.use_days() == 0:
        return "(last used today)"
    elif emote.use_days() == 1:
        return "(last used yesterday)"
    else:
        return f"(last used {emote.use_days()} days ago)"


def get_total(emotes):
    nu = 0
    nr = 0
    for name in emotes:
        nu += emotes[name].usages
        nr += emotes[name].reactions
    return f"Total: {nu} times and {nr} reactions"


async def tell_results(first, emotes, channel, *, allow_unused, show_life):
    names = [name for name in emotes]
    names.sort(key=lambda name: emotes[name].score(), reverse=True)
    res = [first]
    res += [
        f"{get_place(names.index(name))} {name} - "
        f"{get_usage(emotes[name])}"
        f"{get_reactions(emotes[name])}"
        # f"{get_life(emotes[name], show_life)}"
        f"{get_last_used(emotes[name])}"
        for name in names if allow_unused or emotes[name].used()]
    res += [get_total(emotes)]
    response = ""
    for r in res:
        if len(response + "\n" + r) > 2000:
            await channel.send(response)
            response = ""
        response += "\n" + r
    if len(response) > 0:
        await channel.send(response)


# MAIN


async def compute(client, message, args):
    debug(message, f"command '{message.content}'")

    guild = message.guild

    permissions = message.channel.permissions_for(guild.me)
    if not permissions.send_messages:
        debug(message, f"missing 'send_messages' permission")
        await message.author.create_dm()
        await message.author.dm_channel.send(
            f"Hi, this bot doesn\'t have the permission to send a message to"
            f" #{message.channel} in server '{message.guild}'")
        return

    emotes = {str(emoji): Emote(emoji) for emoji in guild.emojis}

    if len(args) == 1:
        async with message.channel.typing():
            nm = 0
            nc = 0
            t0 = datetime.now()
            progress = await message.channel.send(f"```starting analysis...```")
            for channel in guild.text_channels:
                nm1 = await analyse_channel(client, channel, emotes, None, progress, nm, nc)
                if nm1 >= 0:
                    nm += nm1
                    nc += 1
            await progress.delete()
            await tell_results(f"{len(emotes)} emotes in this server ({nc} channels, {nm} messages):",
                               emotes, message.channel, allow_unused=True, show_life=True)
            dt = (datetime.now() - t0).total_seconds()
            debug(message, f"response sent {dt} s -> {nm / dt} m/s")
    elif len(message.mentions) > 0:
        if len(args) > 2:
            await message.channel.send("Too many arguments")
        else:
            member = message.mentions[0]
            nm = 0
            nc = 0
            progress = await message.channel.send(f"```starting analysis...```")
            for channel in guild.text_channels:
                nm1 = await analyse_channel(client, channel, emotes, member, progress, nm, nc)
                if nm1 >= 0:
                    nm += nm1
                    nc += 1
            await progress.delete()
            await tell_results(
                f"{member.mention} emotes usage in {nm} messages:", emotes,
                message.channel, allow_unused=False, show_life=False)
            debug(message, f"response sent")
    elif len(message.channel_mentions) > 0:
        if len(args) > 2:
            await message.channel.send("too many arguments")
        else:
            channel = message.channel_mentions[0]
            progress = await message.channel.send(f"```starting analysis...```")
            nm = await analyse_channel(client, channel, emotes, None, progress, 0, 0)
            await progress.delete()
            if nm < 0:
                await message.channel.send(f"I'm sorry I could not read messages in {channel.mention}")
                debug(message, f"cannot read channel")
                return
            await tell_results(
                f"{channel.mention} emotes usage in {nm} messages:", emotes,
                message.channel, allow_unused=False, show_life=False)
            debug(message, f"response sent")
    elif args[1] == "help":
        await message.channel.send(
            "Emotes Analysis:\n"
            "```"
            "%emotes : Rank emotes by their usage\n"
            "%emotes @user : // for a specific user"
            "%emotes #channel : // for a specific channel"
            "```")
    else:
        await message.channel.send(f"Unknown command : type `%emotes help` for more info")
