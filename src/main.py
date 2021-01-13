from miniscord import Bot
import logging

from utils import emojis
from scanners import (
    EmotesScanner,
    FullScanner,
    FrequencyScanner,
    CompositionScanner,
    PresenceScanner,
    MentionsScanner,
    MentionedScanner,
)
from logs import GuildLogs

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(module)s] %(message)s", level=logging.INFO
)

emojis.load_emojis()

bot = Bot(
    "Discord Analyst",
    "1.7(wip)",
    alias="%",
)

bot.log_calls = True

bot.register_command(
    "(cancel|stop)",
    GuildLogs.cancel,
    "cancel: stop current analysis",
    "```\n" + "%cancel: Stop current analysis\n" + "```",
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
