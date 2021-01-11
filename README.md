[![Scc Count Badge](https://sloc.xyz/github/klemek/discord-analyst/?category=code)](https://github.com/boyter/scc/#badges-beta)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/alerts/)

# Discord Analyst

When you need statistics about your discord server

* `%help (command)` - info about commands
* `%info` - version and uptime
* `%emotes` : Rank emotes by their usage
  * arguments:
    * @member/me : filter for one or more member
    * #channel/here : filter for one or more channel
    * <n> : top <n> emojis, default is 20
    * all : list all common emojis in addition to this guild's
    * members : show top member for each emote
  * Example: `%emotes 10 all #mychannel1 #mychannel2 @user`

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
python3 src/main.py
```

## Changelog

* **(WIP)v1.6**:
  * more scans : `%full`, `%freq`, `%comp`, `%other`
  * huge bug fix
* **v1.5**:
  * top <n> emotes
  * bug fix
* **v1.4**:
  * integrate miniscord
  * insane speed with bot-side logging
  * bug fix
* **v1.3**: revert to v1.1 and update requirements
* **v1.2**: don't quit on occasional exception
* **v1.1**:
  * coma separator for big numbers
  * history loading by chunks for big channels (performance increase)
  * bug fix
* **v1.0**: stable release
