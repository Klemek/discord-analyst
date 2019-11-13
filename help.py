from utils import debug


async def compute(message, args):
    debug(message, f"command '{message.content}'")
    if len(args) > 1 and args[1] == "emotes":
        await message.channel.send(
            "Emotes Analysis:\n"
            "```"
            "%emotes : Rank emotes by their usage\n"
            "%emotes @user : // for a specific user\n"
            "%emotes #channel : // for a specific channel\n"
            "(Add more @user or #channel to be more selective)"
            "```")
        return
    else:
        await message.channel.send(
            "Discord Analyst commands:\n"
            "```"
            "%help (command) : Info on commands\n"
            "%info : This bot info\n"
            "%emotes : Emotes analysis"
            "```")
