# DISCORD API

def debug(message, txt):
    print(f"{message.guild} > #{message.channel}: {txt}")


# LISTS

def no_duplicate(seq):
    return list(dict.fromkeys(seq))


# MESSAGE FORMATTING

def aggregate(names):
    if len(names) == 0:
        return ""
    elif len(names) == 1:
        return names[0]
    else:
        return ", ".join(names[:-1]) + " & " + names[-1]
