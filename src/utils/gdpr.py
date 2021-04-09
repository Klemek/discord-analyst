import discord

from logs import GuildLogs


HELP = (
    "```\n"
    + "%gdpr: Displays GDPR information\n"
    + "arguments:\n"
    + "* agree - agree to GDPR\n"
    + "* revoke - remove this server's data\n"
    + "```"
)

TEXT = (
    ""
    + "__**About Analyst-bot's data usage**__\n"
    + "**TL;DR**\n"
    + "Analyst-bot collects text message information. It does not share collected data with any third-party and data is retained 12 months or until the bot is leaving the guild/server.\n"
    + "**Data collection**\n"
    + "Analyst-bot collects a Discord guild/server's history when asked to.\n"
    + "This includes:\n"
    + "- Visible text channel names\n"
    + "- Visible text messages: date and time of creation and edition,  author,  content,  reactions and other available metadata (pinned, tts, etc.)\n"
    + "This does __not__ includes:\n"
    + "- Voice channels and not visible channels\n"
    + "- Not visible text messages\n"
    + "- Visible text messages' embedded content, images and other attachments\n"
    + "**Data processing**\n"
    + "Any data collected is only processed in order to produce a one-time report sent to the user immediately. No temporary data are retained.\n"
    + "**Data storage and retain policy**\n"
    + "Analyst-bot stores the collected data in files that are accessible by the software and its administrator only.\n"
    + "Any collected data are retained maximum 12 months until deletion or when the bot is leaving a guild/server.\n"
    + "**Data sharing**\n"
    + "Analyst-bot does not share the data collected with any third-party.\n"
    + "**Right to retract**\n"
    + "If you want to have your data removed, you can use the `%gdpr revoke` command or remove this bot from your guild/server.\n"
    + "**Terms agreement**\n"
    + "By agreeing to these terms, you ensure having the legal age if you are in a country that does have one and you also ensure having the consent of every member involved.\n"
    + "\n"
    + "*If you want more information, please contact the creator of this bot: <https://github.com/Klemek/discord-analyst>.*\n"
    + "\n"
    + "Type `%gdpr agree` to agree to these terms, `%gdpr revoke` to remove this guild/server's collected data or `%gdpr` to see this message again."
)

AGREE_TEXT = "Thanks for agreeing for these terms, you can now run analysis on this guild/server."

REVOKE_TEXT = "This guild/server's data has been deleted. To run new analysis you must agree to the terms again."


async def process(client: discord.client, message: discord.Message, *args: str):
    args = list(args)
    if len(args) == 1:
        await message.channel.send(TEXT)
    elif len(args) > 2:
        await message.channel.send(f"Too many arguments", reference=message)
    elif args[1] == "help":
        await message.channel.send(HELP, reference=message)
    elif args[1] in ["agree", "accept"]:
        GuildLogs.init_log(message.channel.guild)
        await message.channel.send(AGREE_TEXT, reference=message)
    elif args[1] in ["revoke", "cancel", "remove", "delete"]:
        GuildLogs.remove_log(message.channel.guild)
        await message.channel.send(REVOKE_TEXT, reference=message)
    else:
        await message.channel.send(
            f"Unrecognized argument: `{args[1]}`", reference=message
        )
