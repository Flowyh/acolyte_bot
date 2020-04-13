from .eco import User, Session, BetEntry
from .eco import Bet as DbBet

import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
import re


def create_user_entry(session, ctx: Context):
    caller: discord.User = ctx.message.author
    db_user = User(nick=caller.name, discord_id=caller.id, guild_id=ctx.guild.id, money=1000)
    session.add(db_user)
    return db_user


USER_ID_RE = re.compile(r"<@!([0-9]*)>")


async def get_user_from_string(ctx, s):
    m = USER_ID_RE.match(s)
    if m:
        user_id = int(m.group(1))
        user = await ctx.bot.fetch_user(user_id)
    else:
        user = discord.utils.get(ctx.guild.members, name=s)
    return user


def database_user(session, u: Union[discord.User, Context], g: discord.Guild = None) -> User:  
    if isinstance(u, Context):
        g = u.guild
        u = u.message.author
    db_user = session.query(User).filter_by(discord_id=u.id).filter_by(guild_id=g.id).first()
    return db_user


class BetMessage:

    bot = None  # This will be initialized when Bet cog is initialized

    async def __init__(self, bet_channel):
        self.message = await bet_channel.send("This is a bet")
        await self.message.pin()

    def resolve(self):
        await self.message.delete()



class Bet(commands.Cog):

    def __init__(self, bot):
        self.bot = bot  # isn't super() call necessary???
        BetMessage.bot = bot  # TODO thats disgusting


    @commands.command(name="register", usage="WIP", bref="WIP")
    async def register(self, ctx: Context):
        session = Session()

        create_user_entry(session, ctx)
        try:
            session.commit()
            await ctx.channel.send("Registration succesful!")
        except Exception as e:
            await self.bot.debug("Error in registration:", e)
            await ctx.channel.send("Registration failed. Contact the administrator")
        
    @commands.command(name="balance", usage="WIP")
    async def balance(self, ctx: Context):
        caller: discord.User = ctx.message.author

        session = Session()

        db_user = session.query(User).filter_by(discord_id=caller.id).first()
        if db_user is None:
            await ctx.channel.send(f"You must register first")

        else:
            balance_ = db_user.money
            await ctx.channel.send(f"Current balance: {balance_}")

    @commands.command(name="transfer", usage="WIP")
    async def transfer(self, ctx: Context, amount: int, recipient_s: str):
        recipient = await get_user_from_string(ctx, recipient_s)
        
        session = Session()
        source = session.query(User).filter_by(discord_id=ctx.message.author.id).first()
        destination = session.query(User).filter_by(discord_id=recipient.id).first()

        source.transfer(amount, destination)
        session.commit()
        await ctx.channel.send("Transfer complete")

    @commands.command(name="newbet", usage="WIP")
    async def newbet(self, ctx: Context, amount: int, description: str):
        session = Session()
        db_user = database_user(session, ctx.message.author)

        b = db_user.create_bet(session, description, amount)

        session.commit()
        await ctx.channel.send(f"New bet created with id {b.id}")

    @commands.command(name="beton", usage="WIP")
    async def beton(self, ctx: Context, bet_id: int, amount: int, outcome: int):
        session = Session()
        db_user = database_user(session, ctx.message.author)

        bet = session.query(DbBet).get(bet_id)
        if bet is None:
            await ctx.channel.send("No such bet")

        else:
            db_user.enter_bet(session, bet, amount, bool(outcome))  # TODO: Check balance

            session.commit()
            await ctx.channel.send("Entry accepted")

    @commands.command(name="resolve", usage="WIP")
    async def resolve(self, ctx: Context, bet_id: int, outcome: int):
        session = Session()
        db_user = database_user(session, ctx.message.author)

        bet = session.query(DbBet).get(bet_id)
        if bet is None:
            await ctx.channel.send("No such bet")
            return

        if bet.creator.id != db_user.id:
            await ctx.channel.send("You are not the original creator")
            return

        bet.resolve(session, bool(outcome))
        session.commit()

        await ctx.channel.send("Bet resolved")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        print(message)
        print(message.content)

def setup(bot):
    bot.add_cog(Bet(bot))
