from miniscord import Bot

import emotes

bot = Bot(
    "Discord Analyst",  # name
    "1.4",  # version
    alias="%",  # respond to '|command' messages
)
bot.log_calls = True
bot.register_command(
    "emotes",  # command text (regex)
    emotes.compute,  # command function
    "emotes: Emotes analysis",  # short help
    "```\n"
    "* %emotes : Rank emotes by their usage\n"
    "* %emotes @user : // for a specific user\n"
    "* %emotes #channel : // for a specific channel\n"
    "(Add more @user or #channel to be more selective)\n"
    "```",
)
bot.start()
