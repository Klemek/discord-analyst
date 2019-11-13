from utils import debug


async def compute(message, args):
    """
    Computes the %help command

    :param message: message sent
    :type message: discord.Message
    :param args: arguments of the command
    :type args: list[str]
    """
    debug(message, f"command '{message.content}'")

    # Select correct response to send

    response = "Discord Analyst commands:\n" \
               "```\n" \
               "%help (command) : Info on commands\n" \
               "%info : This bot info\n" \
               "%emotes : Emotes analysis\n" \
               "```"

    if len(args) > 1 and args[1] == "emotes":
        response = "Emotes Analysis:\n" \
                   "```\n" \
                   "%emotes : Rank emotes by their usage\n" \
                   "%emotes @user : // for a specific user\n" \
                   "%emotes #channel : // for a specific channel\n" \
                   "(Add more @user or #channel to be more selective)\n" \
                   "```"

    await message.channel.send(response)
