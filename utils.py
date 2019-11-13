# DISCORD API

def debug(message, txt):
    """
    Print a log with the context of the current event

    :param message: message that triggered the event
    :type message: discord.Message
    :param txt: text of the log
    :type txt: str
    """
    print(f"{message.guild} > #{message.channel}: {txt}")


# LISTS

def no_duplicate(seq):
    """
    Remove any duplicates on a list

    :param seq: original list
    :type seq: list
    :return: same list with no duplicates
    :rtype: list
    """
    return list(dict.fromkeys(seq))


# MESSAGE FORMATTING

def aggregate(names):
    """
    Aggregate names with , and &

    Example : "a, b, c & d"

    :param names: list of names
    :type names: list[str]
    :return: correct aggregation
    :rtype: str
    """
    if len(names) == 0:
        return ""
    elif len(names) == 1:
        return names[0]
    else:
        return ", ".join(names[:-1]) + " & " + names[-1]
