from discord.ext import commands
from discord.ext.commands import Context
from discord.ext import tasks

from .models import DiscordUser


class UserData(commands.Cog):

    interval_minutes = 10

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.update_users.start()

    def cog_unload(self):
        self.update_users.cancel()

    @tasks.loop(minutes=interval_minutes)
    async def update_users(self):
        print("user update loop running")
        for guild in self.bot.guilds:
            for member in guild.members:
                print("Adding ", member)
                DiscordUser.add_user(member.name, member.id)
        print("user update loop ended")


def setup(bot):
    print("userdata cog loaded")
    bot.add_cog(UserData(bot))
