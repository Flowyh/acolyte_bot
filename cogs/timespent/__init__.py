import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext import tasks
from .models import TimeEntry

from datetime import date, timedelta
import sys

class TimeSpent(commands.Cog):

    interval = 30

    def __init__(self, bot):
        self.bot = bot
        self.update_time_spent.start()

    def cog_unload(self):
        self.update_time_spent.cancel()

    @tasks.loop(seconds=interval)
    async def update_time_spent(self):
        await self.bot.wait_until_ready()

        today = date.today()

        for guild in self.bot.guilds:
            for chan in guild.voice_channels:
                for u in chan.members:
                    TimeEntry.update_user(u.id, chan.id, guild.id, TimeSpent.interval)


    @commands.command(name="timespent", brief="Show summary of time spent on the server by all the users")
    async def time_spent_summary(self, ctx: Context):
        res = TimeEntry.get_summary(ctx.guild.id)

        message = "Time spent on server today:\n\n"
        for u_id, t in res:
            user = await self.bot.fetch_user(u_id)
            td = timedelta(seconds=t)
            message += f"{user}: {td}\n"

        await ctx.channel.send(message)

        print(res)



def setup(bot):
    print("Time cog loadeed")
    bot.add_cog(TimeSpent(bot))
