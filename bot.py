import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DEBUG_IDS = os.getenv('ADMIN_DEBUG_ID').split(":")

bot = commands.Bot(command_prefix='!')

DEBUG_USERS = []

@bot.event
async def on_ready():
    print("Bot starting")
    global DEBUG_USERS
    DEBUG_USERS = [bot.get_user(int(i)) for i in DEBUG_IDS]

# TODO format error exceptions with __repr__ somewhere
# @bot.event
# async def on_command_error(error, *args, **kwargs):
#     print("senging to users:", DEBUG_USERS)
#     for u in DEBUG_USERS:
#         ch = u.dm_channel
#         if ch is None:
#             await u.create_dm()
#             ch = u.dm_channel
#         msg = "```Exception:\nFailed on with error {}\nwith args: {}\n kwargs: {}```".format(error, args, kwargs)
#         await ch.send(msg)
#         print("Sent message\n", msg)

async def debug(msg):
    group = []
    for u in DEBUG_USERS:
        ch = u.dm_channel
        if ch is None:
            await u.create_dm()
            ch = u.dm_channel
        group.append(ch.send(msg))
    await asyncio.gather(*group)

bot.debug = debug


@bot.event
async def on_ready():
    print(f'Bot connected!')


# @bot.event
# async def on_command_error(ctx, error):
#     pass


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


@bot.command()
async def fail(ctx, msg):
    print("Bot failing with msg", msg)
    raise discord.DiscordException("Controlled failure")


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')


@bot.command()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')

bot.load_extension("cogs.vote")
bot.load_extension("cogs.timespent")
bot.load_extension("cogs.bet")

bot.run(TOKEN)
