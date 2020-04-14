from .eco import User, Session, BetEntry
from .eco import Bet as DbBet

import discord
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union
import asyncio
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
    assert u is not None
    assert g is not None
    db_user = session.query(User).filter_by(discord_id=u.id).filter_by(guild_id=g.id).first()
    return db_user


def is_bet_channel(ctx: Context):
    return ctx.channel.name == "bets"


def make_emoji_dict():
    result = {}
    positive_1_code = ord("①")
    negative_1_code = ord("❶")

    for i in [1, 2, 5, 10]:
        result[chr(positive_1_code + (i - 1))] = i * 100
        result[chr(negative_1_code + (i - 1))] = -i * 100
    print(result)
    return result

# EMOJI_DICT = make_emoji_dict()
EMOJI_DICT = {
        "1\u20e3": 100,
        "3\u20e3": 300,
        "5\u20e3": 500,
        "0\u20e3": 1000
}


class BetMessage:

    bot = None  # This will be initialized when Bet cog is initialized

    def __init__(self, bet_channel, message, on_message, against_message, session, model, bot):
        self.bet_channel = bet_channel
        self.description = message.content
        self.message = message
        self.on_message = on_message
        self.against_message = against_message
        self.session = session
        self.model = model

        # TODO reaction betting may have issues with users feedback
        async def handle_reaction(reaction, user):
            print("reaction handler entered")
            if reaction.message.id == self.on_message.id:
                on = True
            elif reaction.message.id == self.against_message.id:
                on = False
            else:
                print("unrelated message")
                return 

            if user.id == bot.user.id:  # Ignore own reactions
                return

            if reaction.emoji in EMOJI_DICT:
                db_user = database_user(self.session, user, self.message.channel.guild)
                if db_user is None:
                    print("user not found: ", user)
                    return

                amount = EMOJI_DICT[reaction.emoji]
                if on:
                    try:
                        self.model.enter_user(self.session, db_user, amount, True)
                        print("User {} entered on W with {}".format(db_user, amount))
                    except ValueError:  # User doesn't have enough money
                        print("User {} tried to enter on W with not enough money".format(db_user))  
                        await reaction.remove(user)  # This clears all reactions, but does not kick user out of a bet
                else:
                    try:
                        print("User {} entered on L with {}".format(db_user, amount))
                        self.model.enter_user(self.session, db_user, amount, False)
                    except ValueError:  # User doesn't have enough money
                        print("User {} tried to enter on L with not enough money".format(db_user))  
                        await reaction.remove(user)
                await self.regenerate_message()
            else:
                print("resolution attempted")
                if user.id == self.model.creator.discord_id:
                    if reaction.message.id == self.on_message.id:
                        outcome = True
                    elif reaction.message.id == self.against_message.id:
                        outcome = False
                    else:
                        return
                    await self.resolve(outcome)
                else:
                    print("unauthorised resolution attempted")
                    print(user, self.model.creator)
                    await reaction.remove(user)  # this clears reactions but does not remove user
                    

        self.listener = handle_reaction

        bot.add_listener(handle_reaction, "on_reaction_add")

    async def regenerate_message(self):
        print("Regenerating message")
        content = self.description.strip("```")
        content += "\n Entries:\n"
        first_on = True
        for e in self.model.entries:
            if e.on != True:
                continue
            if first_on:
                first_on = False
                content += "On:\n"
            content += "{}: {}¤".format(e.user.nick, e.amount)

        first_against = True
        for e in self.model.entries:
            if e.on != False:
                continue
            if first_against:
                first_against = False
                content += "\nAgainst:\n"
            content += "{}: {} ¤".format(e.user.nick, e.amount)

        content = f"```{content}```"
        await self.message.edit(content=content)
        print("Regenaration Complete")

    async def init_emoji(self):
        ordered_list = sorted(EMOJI_DICT.keys(), key=lambda k: EMOJI_DICT[k])
        to_wait = []
        for e in ordered_list:
            to_wait.append(self.on_message.add_reaction(e))
            to_wait.append(self.against_message.add_reaction(e))
        await asyncio.gather(*to_wait)

    @classmethod
    async def new(cls, ctx: Context, description):  # responsibility of the caller to restrict this to a single channel
        session = Session()
        db_user = database_user(session, ctx)
        bet = DbBet(creator=db_user, description=description, active=True)
        session.add(bet)
        session.flush()

        description = f"Bet id: {bet.id}\n" + "Description: " + description
        description = description + "\nTo resolve add any new reaction on \"Bet on/against\" message"
        description = f"```{description}```"
        message = await ctx.channel.send(description)
        on_message = await(ctx.channel.send("Bet on"))
        against_message = await(ctx.channel.send("Bet against"))
        await message.pin()
        res = cls(ctx.channel, message, on_message, against_message, session, bet, ctx.bot)
        await res.regenerate_message()
        await res.init_emoji()

        return res


    async def resolve(self, outcome):
        print("resolve promped")
        self.model.resolve(self.session, outcome)
        self.bot.remove_listener(self.listener)
        self.session.commit()
        await asyncio.gather(self.message.delete(), self.on_message.delete(), self.against_message.delete())


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

        db_user = database_user(session, ctx)
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
    @commands.check(is_bet_channel)
    async def newbet(self, ctx: Context, description: str):
        bm = await BetMessage.new(ctx, description)

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


def setup(bot):
    bot.add_cog(Bet(bot))
