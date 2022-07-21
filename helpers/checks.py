def is_author(author):
    """
    This is a custom check to see if the user sending message is the author of the message that the bot is waiting an answer for.
    """

    def inner_check(message):
        return message.author == author

    return inner_check


def reaction_check(client, messageId):
    """
    This is a custom check to see if the user reacts with ✅ to a message.
    """

    def inner_check(reaction, user):
        return client.user != user and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == messageId

    return inner_check


def is_tw(message):
    keywords = ["suicide", "kill", "depression", "traumatised", "phobia", "panic", "murder", "rape"]

    for keyword in keywords:
        if keyword in message:
            return True

    return False
