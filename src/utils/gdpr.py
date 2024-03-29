import discord

from logs import GuildLogs


HELP = """```
%gdpr: Displays GDPR information
arguments:
* agree - agree to GDPR
* revoke - remove this server's data
```"""

TEXT = """
__**About Analyst-bot's data usage**__
**TL;DR**
Analyst-bot collects text message information. It does not share collected data with any third-party and data is retained 90 days or until the bot is leaving the guild/server.
**Data collection**
Analyst-bot collects a Discord guild/server's history when asked to.
This includes:
- Visible text channel names
- Visible text messages: date and time of creation and edition,  author,  content,  reactions and other available metadata (pinned, tts, etc.)
This does __not__ includes:
- Voice channels and not visible channels
- Not visible text messages
- Visible text messages' embedded content, images and other attachments
**Data processing**
Any data collected is only processed in order to produce a one-time report sent to the user immediately. No temporary data are retained.
**Data storage and retain policy**
Analyst-bot stores the collected data in files that are accessible by the software and its administrator only.
Any collected data are retained maximum 90 days until deletion or when the bot is leaving a guild/server.
**Data sharing**
Analyst-bot does not share the data collected with any third-party.
**Right to retract**
If you want to have your data removed, you can use the `%gdpr revoke` command or remove this bot from your guild/server.
**Terms agreement**
By agreeing to these terms, you ensure having the legal age if you are in a country that does have one and you also ensure having the consent of every member involved.

*If you want more information, please contact the creator of this bot: <https://github.com/Klemek/discord-analyst>.*

Type `%gdpr agree` to agree to these terms, `%gdpr revoke` to remove this guild/server's collected data or `%gdpr` to see this message again.
"""

AGREE_TEXT = "Thanks for agreeing for these terms, you can now run analysis on this guild/server."

REVOKE_TEXT = "This guild/server's data has been deleted. To run new analysis you must agree to the terms again."


async def process(client: discord.client, message: discord.Message, *args: str):
    args = list(args)
    if len(args) == 1:
        await message.channel.send(TEXT)
    elif args[1] == "help":
        await client.bot.help(client, message, "help", args[0])
    elif len(args) > 2:
        await message.channel.send(f"Too many arguments", reference=message)
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
