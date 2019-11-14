[![Scc Count Badge](https://sloc.xyz/github/klemek/discord-analyst/?category=code)](https://github.com/boyter/scc/#badges-beta)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/alerts/)

# Discord Analyst

When you need statistics about your discord server

* `%help (command)` - info about commands
* `%info` - version and uptime
* `%emotes` - gives you a full ranking of the server emotes by usage
  *  Be more specific by adding some `@member` or `#channel` in arguments

## Running this bot

**1. Install requirements**

```
pip3 install -r requirements.txt
```

**2. Make a .env file as following**

```
#.env
DISCORD_TOKEN=<bot token from discordapp.com/developers>
```

**3.Invite bot in your discord server**

Generate and use the OAuth2 link in [discordapp.com/developers](https://discordapp.com/developers) to invite it.

You will need:
* Scopes:
  * bot
* Bot Permissions:
  * View Channels
  * Send Messages
  * Read Message History

**4. Launch bot**

```
python3 bot.py
```

## Changelog

* **v1.1**:
  * coma separator for big numbers
  * history loading by chunks for big channels (performance increase)
  * bug fix
* **v1.0**: stable release
