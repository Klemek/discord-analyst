from miniscord import Bot

import emotes

bot = Bot(
    "Discord Analyst",  # name
    "1.4",  # version
    alias="%",  # respond to '|command' messages
)
bot.log_calls = True
bot.client.bot = bot  # TODO place in miniscord
bot.register_command(
    "emotes",  # command text (regex)
    emotes.compute,  # command function
    "emotes: Emotes analysis",  # short help
    emotes.HELP,
)
bot.start()
