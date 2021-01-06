from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import discord
import re
import json

# Custom libs
from utils import debug, aggregate, no_duplicate

# preload

EXTRA_EMOJI = {
    "thumbup": "1f44d",
    "thumbdown": "1f44e",
    "timer": "23f2-fe0f",
    "cowboy": "1f920",
    "clown": "1f921",
    "newspaper2": "1f5de-fe0f",
    "french_bread": "1f956",
    "nerd": "1f913",
    "zipper_mouth": "1f910",
    "salad": "1f957",
    "rolling_eyes": "1f644",
    "basketball_player": "26f9-fe0f-200d-2642-fe0f",
    "thinking": "1f914",
    "e_mail": "2709-fe0f",
    "slight_frown": "1f641",
    "skull_crossbones": "2620-fe0f",
    "hand_splayed": "1f590-fe0f",
    "speaking_head": "1f5e3-fe0f",
    "cross": "271d-fe0f",
    "crayon": "1f58d-fe0f",
    "head_bandage": "1f915",
    "rofl": "1f923",
    "flag_white": "1f3f3-fe0f",
    "slight_smile": "1f642",
    "fork_knife_plate": "1f37d-fe0f",
    "robot": "1f916",
    "hugging": "1f917",
    "biohazard": "2623-fe0f",
    "notepad_spiral": "1f5d2-fe0f",
    "lifter": "1f3cb-fe0f-200d-2642-fe0f",
    "race_car": "1f3ce-fe0f",
    "left_facing_fist": "1f91b",
    "right_facing_fist": "1f91c",
    "tools": "1f6e0-fe0f",
    "umbrella2": "2602-fe0f",
    "upside_down": "2b07-fe0f",
    "first_place": "1f947",
    "dagger": "1f5e1-fe0f",
    "fox": "1f98a",
    "menorah": "1f54e",
    "desktop": "1f5a5-fe0f",
    "motorcycle": "1f3cd-fe0f",
    "levitate": "1f574-fe0f",
    "cheese": "1f9c0",
    "fingers_crossed": "1f91e",
    "frowning2": "1f626",
    "microphone2": "1f399-fe0f",
    "flag_black": "1f3f4",
    "chair": "1FA91",
}

GLOBAL_EMOJIS = {}
EMOJI_REGEX = re.compile("(<a?:\\w+:\\d+>|:\\w+:)")


def load_emojis():
    global GLOBAL_EMOJIS, INV_GLOBAL_EMOJIS, EMOJI_REGEX
    emoji_list = []
    with open("emoji.json") as f:
        emoji_list = json.loads(f.readline().strip())
    for emoji in EXTRA_EMOJI:
        emoji_list += [{"short_name": emoji, "unified": EXTRA_EMOJI[emoji]}]
    unicode_list = []
    for emoji in emoji_list:
        shortcode = emoji["short_name"]
        unified = emoji["unified"]
        if unified is not None and shortcode is not None:
            unicode_escaped = "".join([f"\\U{c:0>8}" for c in unified.split("-")])
            unicode = bytes(unicode_escaped, "ascii").decode("unicode-escape")
            shortcode = f":{shortcode.replace('-','_')}:"
            GLOBAL_EMOJIS[unicode] = shortcode
            unicode_list += [unicode_escaped]
    EMOJI_REGEX = re.compile(f"(<a?:\\w+:\\d+>|:\\w+:|{'|'.join(unicode_list)})")


load_emojis()
print(f"loaded {len(GLOBAL_EMOJIS)} emojis")

# CONSTANTS

CHUNK_SIZE = 10000


# MAIN

HELP = (
    "```\n"
    + "%emotes : Rank emotes by their usage\n"
    + "arguments:\n"
    + "* @member : filter for one or more member\n"
    + "* #channel : filter for one or more channel\n"
    + "* reactions : add reaction analysis for members (long)\n"
    + "* all : list all common emojis in addition to this guild's\n"
    + "```"
)


async def compute(client: discord.client, message: discord.Message, *args: str):
    """
    Computes the %emotes command
    """
    guild = message.guild

    # If "%emotes help" redirect to "%help emotes"
    if "help" in args:
        await client.bot.help(client, message, "help", "emotes")
        return

    # Create emotes dict from custom emojis of the guild
    emotes = defaultdict(Emote)
    for emoji in guild.emojis:
        emotes[str(emoji)] = Emote(emoji)

    # Get selected channels or all of them if no channel arguments
    channels = no_duplicate(message.channel_mentions)
    full = len(channels) == 0
    if full:
        channels = guild.text_channels

    # Get selected members
    members = no_duplicate(message.mentions)

    # Start computing data
    async with message.channel.typing():
        nm = 0  # number of messages treated
        nmm = 0  # number of impacted messages
        nc = 0  # number of channel treated
        t0 = datetime.now()
        # Show custom progress message and keep it to update it later
        progress = await message.channel.send("```starting analysis...```")
        # Analyse every channel selected
        for channel in channels:
            nm1, nmm1 = await analyse_channel(
                channel,
                emotes,
                members,
                progress,
                nm,
                nc,
                all_emojis="all" in args,
                analyse_members_reactions="reactions" in args,
            )
            # If treatment was successful, increase numbers
            if nm1 >= 0:
                nm += nm1
                nmm += nmm1
                nc += 1
        # Delete custom progress message
        await progress.delete()
        # Display results
        await tell_results(
            get_intro(emotes, full, channels, members, nmm, nc),
            emotes,
            message.channel,
            nmm,
            allow_unused=full and len(members) == 0,
            show_life=False,
        )
        dt = (datetime.now() - t0).total_seconds()
        debug(message, f"response sent {dt} s -> {nm / dt} m/s")


# CLASSES


class Emote:
    """
    Custom class to store emotes data
    """

    def __init__(self, emoji: Optional[discord.Emoji] = None):
        self.emoji = emoji
        self.usages = 0
        self.reactions = 0
        self.last_used = None

    def update_use(self, date: datetime):
        """
        Update last use date if more recent
        """
        if self.last_used is None or date > self.last_used:
            self.last_used = date

    def used(self) -> bool:
        return self.usages > 0 or self.reactions > 0

    def score(self) -> float:
        # Score is compose of usages + reactions
        # When 2 emotes have the same score,
        # the days since last use is stored in the digits
        # (more recent first)
        return self.usages + self.reactions + 1 / (100000 * (self.use_days() + 1))

    def life_days(self) -> int:
        return (datetime.today() - self.emoji.created_at).days

    def use_days(self) -> int:
        # If never used, use creation date instead
        if self.last_used is None:
            return self.life_days()
        else:
            return (datetime.today() - self.last_used).days


# ANALYSIS


async def analyse_channel(
    channel: discord.TextChannel,
    emotes: Dict[str, Emote],
    members: List[discord.Member],
    progress: discord.Message,
    nm0: int,  # number of already analysed messages
    nc: int,  # number of already analysed channels,
    *,
    all_emojis: bool,
    analyse_members_reactions: bool,
) -> Tuple[int, int]:
    nm = 0
    nmm = 0
    try:
        messages = [None]
        while len(messages) >= CHUNK_SIZE or messages[-1] is None:
            messages = await channel.history(
                limit=CHUNK_SIZE, before=messages[-1]
            ).flatten()
            for m in messages:
                # If author is not bot or included in the selection (empty list is all)
                if not m.author.bot and (len(members) == 0 or m.author in members):
                    # Find all emotes un the current message in the form "<:emoji:123456789>"
                    # Filter for known emotes
                    found = EMOJI_REGEX.findall(m.content)
                    # For each emote, update its usage
                    for name in found:
                        if name not in emotes:
                            if not all_emojis or name not in GLOBAL_EMOJIS:
                                continue
                            name = GLOBAL_EMOJIS[name]
                        emotes[name].usages += 1
                        emotes[name].update_use(m.created_at)
                    # Count this message as impacted
                    nmm += 1

                # For each reaction of this message, test if known emote and update when it's the case
                for reaction in m.reactions:
                    name = str(reaction.emoji)
                    if name not in emotes:
                        if not all_emojis or name not in GLOBAL_EMOJIS:
                            continue
                        name = GLOBAL_EMOJIS[name]
                    if len(members) == 0:
                        emotes[name].reactions += reaction.count
                        emotes[name].update_use(m.created_at)
                    elif analyse_members_reactions:
                        users = await reaction.users().flatten()
                        for member in members:
                            if member in users:
                                emotes[name].reactions += 1
                                emotes[name].update_use(m.created_at)
            nm += len(messages)
            await progress.edit(
                content=f"```{nm0 + nm:,} messages and {nc} channels analysed```"
            )
        return nm, nmm
    except discord.errors.HTTPException:
        # When an exception occurs (like Forbidden) sent -1
        return -1, -1


# RESULTS


async def tell_results(
    intro: str,  # introduction sentence (from get_intro)
    emotes: Dict[str, Emote],
    channel: discord.TextChannel,
    nmm: int,  # number of impacted messages
    *,
    allow_unused: bool,
    show_life: bool,
):
    names = [name for name in emotes]
    names.sort(key=lambda name: emotes[name].score(), reverse=True)
    res = [intro]
    res += [
        f"{get_place(names.index(name))} {name} - "
        f"{get_usage(emotes[name])}"
        f"{get_reactions(emotes[name])}"
        f"{get_life(emotes[name], show_life)}"
        f"{get_last_used(emotes[name])}"
        for name in names
        if allow_unused or emotes[name].used()
    ]
    res += [get_total(emotes, nmm)]
    response = ""
    for r in res:
        if len(response + "\n" + r) > 2000:
            await channel.send(response)
            response = ""
        response += "\n" + r
    if len(response) > 0:
        await channel.send(response)


def get_intro(
    emotes: Dict[str, Emote],
    full: bool,
    channels: List[discord.TextChannel],
    members: List[discord.Member],
    nmm: int,  # number of messages impacted
    nc: int,  # number of channels analysed
) -> str:
    """
    Get the introduction sentence of the response
    """
    # Show all data (members, channels) when it's less than 5 units
    if len(members) == 0:
        # Full scan of the server
        if full:
            return f"{len(emotes)} emotes in this server ({nc} channels, {nmm:,} messages):"
        elif len(channels) < 5:
            return f"{aggregate([c.mention for c in channels])} emotes usage in {nmm:,} messages:"
        else:
            return f"These {len(channels)} channels emotes usage in {nmm:,} messages:"
    elif len(members) < 5:
        if full:
            return f"{aggregate([m.mention for m in members])} emotes usage in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"{aggregate([m.mention for m in members])} on {aggregate([c.mention for c in channels])} "
                f"emotes usage in {nmm:,} messages:"
            )
        else:
            return (
                f"{aggregate([m.mention for m in members])} on these {len(channels)} channels "
                f"emotes usage in {nmm:,} messages:"
            )
    else:
        if full:
            return f"These {len(members)} members emotes usage in {nmm:,} messages:"
        elif len(channels) < 5:
            return (
                f"These {len(members)} members on {aggregate([c.mention for c in channels])} "
                f"emotes usage in {nmm:,} messages:"
            )
        else:
            return (
                f"These {len(members)} members on these {len(channels)} channels "
                f"emotes usage in {nmm:,} messages:"
            )


def get_place(i: int) -> str:
    """
    Get the correct rank displayed (1st to 3rd have an emoji)
    """
    if i == 0:
        return ":first_place:"
    if i == 1:
        return ":second_place:"
    if i == 2:
        return ":third_place:"
    return f"**#{i + 1}**"


def get_usage(emote: Emote) -> str:
    """
    Get the correct usage displayed
    """
    if emote.usages == 0 and emote.reactions == 0:
        return "never used "
    elif emote.usages == 1:
        return "1 time "
    else:
        return f"{emote.usages:,} times "


def get_reactions(emote: Emote) -> str:
    """
    Get the correct reactions displayed
    """
    if emote.reactions == 0:
        return ""
    elif emote.reactions == 1:
        return "and 1 reaction "
    else:
        return f"and {emote.reactions:,} reactions "


def get_life(emote: Emote, show_life: bool) -> str:
    """
    Get the correct life span displayed
    """
    if not show_life or emote.default:
        return ""
    else:
        return f"(in {emote.life_days()} days) "


def get_last_used(emote: Emote) -> str:
    """
    Get the correct "last used" displayed
    """
    if emote.usages == 0 and emote.reactions == 0:
        return ""
    elif emote.use_days() == 0:
        return "(last used today)"
    elif emote.use_days() == 1:
        return "(last used yesterday)"
    else:
        return f"(last used {emote.use_days()} days ago)"


def get_total(emotes: Dict[str, Emote], nmm: int) -> str:
    """
    Get the total of all emotes used
    """
    nu = 0
    nr = 0
    for name in emotes:
        nu += emotes[name].usages
        nr += emotes[name].reactions
    if nr > 0:
        return f"Total: {nu:,} times ({nu / nmm:.4f} / message) and {nr:,} reactions"
    else:
        return f"Total: {nu:,} times ({nu / nmm:.4f} / message)"
