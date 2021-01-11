from miniscord import Bot
import logging

from utils import emojis
from scanners import EmotesScanner, FrequencyScanner, CompositionScanner, OtherScanner

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(module)s] %(message)s", level=logging.INFO
)

emojis.load_emojis()

bot = Bot(
    "Discord Analyst",
    "1.6(wip)",
    alias="%",
)

bot.log_calls = True
bot.client.bot = bot  # TODO place in miniscord

bot.register_command(
    "other",
    lambda *args: OtherScanner().compute(*args),
    "other: other data analysis",
    OtherScanner.help(),
)
bot.register_command(
    "emotes",
    lambda *args: EmotesScanner().compute(*args),
    "emotes: emotes analysis",
    EmotesScanner.help(),
)
bot.register_command(
    "comp(osition)?",
    lambda *args: CompositionScanner().compute(*args),
    "comp: composition analysis",
    CompositionScanner.help(),
)
bot.register_command(
    "freq(ency)?",
    lambda *args: FrequencyScanner().compute(*args),
    "freq: frequency analysis",
    FrequencyScanner.help(),
)

bot.start()
