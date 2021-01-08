from miniscord import Bot
import logging

from utils import emojis
from scanners import EmotesScanner

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(module)s] %(message)s", level=logging.INFO
)

emojis.load_emojis()

bot = Bot(
    "Discord Analyst",  # name
    "1.6",  # version
    alias="%",  # respond to '|command' messages
)
bot.log_calls = True
bot.client.bot = bot  # TODO place in miniscord
bot.register_command(
    "emotes",  # command text (regex)
    lambda *args: EmotesScanner().compute(*args),  # command function
    "emotes: Emotes analysis",  # short help
    EmotesScanner.help(),
)
bot.start()
