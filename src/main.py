import sys
from miniscord import Bot
import logging

if sys.version_info < (3, 7):
    print("Please upgrade your Python version to 3.7.0 or higher")
    sys.exit(1)

from utils import emojis, gdpr, command_cache
import scanners
from logs import GuildLogs

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(module)s] %(message)s", level=logging.INFO
)

emojis.load_emojis()

bot = Bot(
    "Discord Analyst",
    "1.17.1",
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
    lambda *args: scanners.WordsScanner().compute(*args),
    "words: (BETA) rank words by their usage",
    scanners.WordsScanner.help(),
)
bot.register_command(
    "repeat",
    command_cache.repeat,
    "repeat: repeat last analysis (adding supplied arguments)",
    "```\n%repeat: repeat last analysis (adding supplied arguments)\n```",
)
bot.register_command(
    "mobile",
    lambda *args: command_cache.repeat(*args, add_args=["mobile"]),
    "mobile: fix @invalid-user for last command but mentions users",
    "```\n%mobile: fix @invalid-user for last command but mentions users\n```",
)
bot.register_command(
    "find",
    lambda *args: scanners.FindScanner().compute(*args),
    "find: find specific words or phrases",
    scanners.FindScanner.help(),
)
bot.register_command(
    "last",
    lambda *args: scanners.LastScanner().compute(*args),
    "last: read last message",
    scanners.LastScanner.help(),
)
bot.register_command(
    "(rand(om)?|mood)",
    lambda *args: scanners.RandomScanner().compute(*args),
    "rand: read a random message",
    scanners.RandomScanner.help(),
)
bot.register_command(
    "first",
    lambda *args: scanners.FirstScanner().compute(*args),
    "first: read first message",
    scanners.FirstScanner.help(),
)
bot.register_command(
    "mentioned",
    lambda *args: scanners.MentionedScanner().compute(*args),
    "mentioned: rank specific user mentions by their usage",
    scanners.MentionedScanner.help(),
)
bot.register_command(
    "(mentions?)",
    lambda *args: scanners.MentionsScanner().compute(*args),
    "mentions: rank mentions by their usage",
    scanners.MentionsScanner.help(),
)
bot.register_command(
    "(emojis?|emotes?)",
    lambda *args: scanners.EmojisScanner().compute(*args),
    "emojis: rank emojis by their usage",
    scanners.EmojisScanner.help(),
)
bot.register_command(
    "(react(ions?)?)",
    lambda *args: scanners.ReactionsScanner().compute(*args),
    "react: rank users by their reactions",
    scanners.ReactionsScanner.help(),
)
bot.register_command(
    "(channels?|chan)",
    lambda *args: scanners.ChannelsScanner().compute(*args),
    "chan: rank channels by their messages",
    scanners.ChannelsScanner.help(),
)
bot.register_command(
    "(messages?|msg)",
    lambda *args: scanners.MessagesScanner().compute(*args),
    "msg: rank users by their messages",
    scanners.MessagesScanner.help(),
)
bot.register_command(
    "pres(ence)?",
    lambda *args: scanners.PresenceScanner().compute(*args),
    "pres: presence analysis",
    scanners.PresenceScanner.help(),
)
bot.register_command(
    "compo(sition)?",
    lambda *args: scanners.CompositionScanner().compute(*args),
    "compo: composition analysis",
    scanners.CompositionScanner.help(),
)
bot.register_command(
    "freq(ency)?",
    lambda *args: scanners.FrequencyScanner().compute(*args),
    "freq: frequency analysis",
    scanners.FrequencyScanner.help(),
)
bot.register_command(
    "(full|scan)",
    lambda *args: scanners.FullScanner().compute(*args),
    "scan: full analysis",
    scanners.FullScanner.help(),
)

bot.start()
