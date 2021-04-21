import sys
from miniscord import Bot
import logging

if sys.version_info < (3, 7):
    print("Please upgrade your Python version to 3.7.0 or higher")
    sys.exit(1)

from utils import emojis, gdpr
from scanners import (
    EmotesScanner,
    FullScanner,
    FrequencyScanner,
    CompositionScanner,
    PresenceScanner,
    MentionsScanner,
    MentionedScanner,
    MessagesScanner,
    ChannelsScanner,
    ReactionsScanner,
    FirstScanner,
    RandomScanner,
    LastScanner,
    WordsScanner,
)
from logs import GuildLogs

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(module)s] %(message)s", level=logging.INFO
)

emojis.load_emojis()

bot = Bot(
    "Discord Analyst",
    "1.14",
    alias="%",
)

bot.log_calls = True


async def on_ready():
    GuildLogs.check_logs(bot.client.guilds)
    return True


async def on_guild_remove():
    GuildLogs.check_logs(bot.client.guilds)
    return True


bot.register_event(on_ready)
bot.register_event(on_guild_remove)

bot.register_command(
    "(cancel|stop)",
    GuildLogs.cancel,
    "cancel: stop current analysis (not launched with fast)",
    "```\n%cancel: Stop current analysis (not launched with fast)\n```",
)
bot.register_command(
    "gdpr",
    gdpr.process,
    "gdpr: displays GDPR information",
    gdpr.HELP,
)
bot.register_command(
    "words",
    lambda *args: WordsScanner().compute(*args),
    "words: (BETA) rank words by their usage",
    WordsScanner.help(),
)
bot.register_command(
    "last",
    lambda *args: LastScanner().compute(*args),
    "last: read last message",
    LastScanner.help(),
)
bot.register_command(
    "rand(om)?",
    lambda *args: RandomScanner().compute(*args),
    "rand: read a random message",
    RandomScanner.help(),
)
bot.register_command(
    "first",
    lambda *args: FirstScanner().compute(*args),
    "first: read first message",
    FirstScanner.help(),
)
bot.register_command(
    "mentioned",
    lambda *args: MentionedScanner().compute(*args),
    "mentioned: rank specific user mentions by their usage",
    MentionedScanner.help(),
)
bot.register_command(
    "(mentions?)",
    lambda *args: MentionsScanner().compute(*args),
    "mentions: rank mentions by their usage",
    MentionsScanner.help(),
)
bot.register_command(
    "(emojis?|emotes?)",
    lambda *args: EmotesScanner().compute(*args),
    "emojis: rank emojis by their usage",
    EmotesScanner.help(),
)
bot.register_command(
    "(react(ions?)?)",
    lambda *args: ReactionsScanner().compute(*args),
    "react: rank users by their reactions",
    ReactionsScanner.help(),
)
bot.register_command(
    "(channels?|chan)",
    lambda *args: ChannelsScanner().compute(*args),
    "chan: rank channels by their messages",
    ChannelsScanner.help(),
)
bot.register_command(
    "(messages?|msg)",
    lambda *args: MessagesScanner().compute(*args),
    "msg: rank users by their messages",
    MessagesScanner.help(),
)
bot.register_command(
    "pres(ence)?",
    lambda *args: PresenceScanner().compute(*args),
    "pres: presence analysis",
    PresenceScanner.help(),
)
bot.register_command(
    "compo(sition)?",
    lambda *args: CompositionScanner().compute(*args),
    "compo: composition analysis",
    CompositionScanner.help(),
)
bot.register_command(
    "freq(ency)?",
    lambda *args: FrequencyScanner().compute(*args),
    "freq: frequency analysis",
    FrequencyScanner.help(),
)
bot.register_command(
    "(full|scan)",
    lambda *args: FullScanner().compute(*args),
    "scan: full analysis",
    FullScanner.help(),
)

bot.start()
