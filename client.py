import json
import os
import random
import platform
import sys

import discord
from discord.ext import tasks
from discord.ext.commands import Bot

from helpers.checks import is_tw, reaction_check


if not os.path.isfile("credentials.json"):
    sys.exit("'credentials.json' not found! Please add it and try again.")
else:
    with open("credentials.json") as file:
        credentials = json.load(file)

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

if not os.path.isfile("confessions.json"):
    sys.exit("'confessions.json' not found! Please add it and try again.")


intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

client = Bot(command_prefix=config["prefix"], intents=intents)
# Removes the default help command of discord.py to be able to create our custom help command.
client.remove_command("help")


@client.event
async def on_ready() -> None:
    """
    The code in this even is executed when the client is ready
    """
    print(f"Logged in as {client.user.name}")
    print(f"Discord API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")
    status_task.start()


@tasks.loop(minutes=1.0)
async def status_task() -> None:
    """
    Setup the game status task of the client
    """

    statuses = ["doing gossips"]
    await client.change_presence(activity=discord.Game(random.choice(statuses)))


@client.event
async def on_message(message: discord.Message) -> None:
    """
    The code in this event is executed every time someone sends a message, with or without the prefix
    :param message: The message that was sent.
    """

    member = message.author

    if not os.path.isfile("confessions.json"):
        sys.exit("'confessions.json' not found! Please add it and try again.")
    else:
        with open("confessions.json") as file:
            confessions = json.load(file)

    # check if author is not the bot itself
    if member == client.user or member.bot:
        return

    # check if it is a Thread
    if isinstance(message.channel, discord.channel.Thread):
        if str(member.id) in confessions:
            if message.channel.id in confessions[str(member.id)]:
                await message.delete()
                await message.channel.send(message.content)
        return

    try:
        # check the channel where the message was sent
        if message.channel.name == config["confessionsChannelName"]:
            await message.delete()

            msg = await member.send(config["askSpillBeans"])

            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            confirmation = await client.wait_for("reaction_add", check=reaction_check(client, msg.id))

            if confirmation[0].emoji == "✅":
                checkChannel = discord.utils.get(client.get_all_channels(), name=config["confessionsCheckChannelName"])
                checkMsg = await checkChannel.send(f"**Review the following bean :**\n{message.content}")

                await checkMsg.add_reaction("✅")
                await checkMsg.add_reaction("❌")

                adminConfirmation = await client.wait_for("reaction_add", check=reaction_check(client, checkMsg.id))

                if adminConfirmation[0].emoji == "✅":
                    count = 0
                    async for _ in message.channel.history(limit=None):
                        count += 1

                    tw = is_tw(message.content)

                    if tw:
                        twMessage = config["twMessage"]
                        beanMsg = await message.channel.send(f"**Bean-{count}**\n{twMessage}")

                        thread = await message.channel.create_thread(
                            message=beanMsg, name=f"Bean-{count}", auto_archive_duration=24 * 60
                        )

                        await thread.send(message.content)
                    else:
                        beanMsg = await message.channel.send(f"**Bean-{count}**\n{message.content}")

                        thread = await message.channel.create_thread(
                            message=beanMsg, name=f"Bean-{count}", auto_archive_duration=24 * 60
                        )

                    await member.send(f"Just spilled the beans as **Bean-{count}**")
                    await checkChannel.send(f"Just spilled the beans as **Bean-{count}**")

                    if str(member.id) in confessions:
                        confessions[str(member.id)].append(thread.id)
                    else:
                        confessions[str(member.id)] = [thread.id]

                    with open("confessions.json", "w", encoding="utf-8") as file:
                        json.dump(confessions, file, ensure_ascii=False, indent=4)
                else:
                    await member.send(f"Your bean was not approved by the staff. Try to write another one!")
                    await checkChannel.send(f"Bean not sent !")

            else:
                await member.send(config["noSpillBeans"])

    except KeyError:
        return


# Run the bot with the token
client.run(credentials["token"])
