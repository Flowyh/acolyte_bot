import discord
import asyncio


def find_role(guild: discord.Guild, given_role: str):
    """
    Finds given role in guild's roles.
    If it is found: returns role.
    If not: returns 0
    """
    found_role = discord.Role
    for role in guild.roles:
        if role.name == given_role:
            found_role = role
            break
    if found_role.name == given_role:
        return found_role
    else:
        raise ValueError('Role not found!')


async def add_reactions_to_msg(msg: discord.Message, reactions: list):
    """
    Adds reactions to given message.
    """
    for react in reactions:
        await msg.add_reaction(react)


async def timer_msg(origin: discord.Message, time: int):
    """
    Creates and sends a timed message.
    Displays how many seconds are left and deletes itself afterwards.
    """
    channel = origin.channel
    timer = await channel.send(f'{time} seconds left!')
    while time != 0:
        time -= 1
        await asyncio.sleep(1)
        await timer.edit(content=f'{time} seconds left!')
    await timer.delete()