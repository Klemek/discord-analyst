![Python Version >= 3.7](https://img.shields.io/badge/python-%3E=3.7%20-blue)
[![Scc Count Badge](https://sloc.xyz/github/klemek/discord-analyst/?category=code)](https://github.com/boyter/scc/#badges-beta)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/Klemek/discord-analyst.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Klemek/discord-analyst/alerts/)
[![Discord Bots](https://top.gg/api/widget/status/643808410495615006.svg)](https://top.gg/bot/643808410495615006)

# Discord Analyst

#### 📈 Gives you precisions you never asked for.

![preview](https://user-images.githubusercontent.com/12103162/111427226-1823ac80-86f6-11eb-9581-fada2db43143.png)

## All commands
```
* %help (command) - info about commands
* %info - version and uptime
* %scan - full analysis
* %freq - frequency analysis
* %compo - composition analysis
* %pres - presence analysis
* %first - read first message
* %rand - read a random message
* %last - read last message
* %gdpr - displays GDPR information
* %emojis - rank emotes by their usage
  * arguments:
    * <n> - top <n> emojis, default is 20
    * all - list all common emojis in addition to this guild's
    * members - show top member for each emote
    * sort:usage/reaction - other sorting methods
* %mentions - rank mentions by their usage
  * arguments:
    * <n> - top <n> mentions, default is 10
    * all - show role/channel/everyone/here mentions
* %mentioned - rank specific user mentions by their usage
  * arguments:
    * <n> - top <n> mentions, default is 10
* %msg - rank users by their messages
  * arguments:
    * <n> - top <n> messages, default is 10
* %chan - rank channels by their messages
  * arguments:
    * <n> - top <n> channels, default is 10
* %react - rank users by their reactions
  * arguments:
    * <n> - top <n> messages, default is 10
* %words - (BETA) rank words by their usage
  * arguments:
    * <n> - words containings <n> or more letters, default is 3
    * <n2> - top <n2> words, default is 10
* %cancel - cancel current analysis (not launched with fast)

* Common arguments:
    * @member/me: filter for one or more member
    * #channel/here: filter for one or more channel
    * <date1> - filter after <date1>
    * <date2> - filter before <date2>
    * all/everyone - include bots messages
    * fast: only read cache
    * fresh: does not read cache
    * mobile/mention: mentions users (fix @invalid-user bug)

(Sample dates: 2020 / 2021-11 / 2021-06-28 / 2020-06-28T23:00 / today / week / 8days / 1y)
```

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

## Recommended permissions

- [x] View Channels
- [x] Read Message History
- [x] Send Messages

> On large servers, you should disable "Send Messages" and enable it on an read-only channel where only administrators can launch commands. The bot can't be triggered elsewhere if it can't answer.

## Already hosted bot

[![Discord Bots](https://top.gg/api/widget/643808410495615006.svg)](https://top.gg/bot/643808410495615006)

## Changelog

* **v1.14**
  * `mobile/mention` arg to fix mobile bug
* **v1.13**
  * improved scan `%words`
  * remove old and unused logs at start and guild leaving
  * GDPR disclaimer before scanning
  * start and stop dates
  * bug fix and improvements
* **v1.12**
  * more scans: `%words`
  * concurrent `fast` analysis
  * assume `fast` if last analysis is fresh
  * better memory handling
  * bug fix
* **v1.11**
  * more scans: `%first`, `%rand`, `%last`
  * streak computing in `%pres`
* **v1.10**
  * multithreading for queries
  * bug fix
* **v1.9**:
  * `all/everyone` to include bots in scans
  * `fresh` to not use previously cached data
  * bug fix
* **v1.8**:
  * more scans: `%msg`, `%chan`
  * bug fix
* **v1.7**:
  * emojis percents
  * emojis other sorting
  * mentions/mentioned ranking
  * `%cancel`
* **v1.6**:
  * more scans: `%scan`, `%freq`, `%compo`, `%pres`
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
