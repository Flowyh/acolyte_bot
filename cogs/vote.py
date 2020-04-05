import discord
from discord.ext import commands
import asyncio


class Vote(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='votekick', usage='{@user} {time in seconds}',
                      brief='Vote to kick specified user. More info !help votekick',
                      help='Vote to kick desired user. Passes only if 2/3 vc members voted for yes. '
                           '30 min cooldown per user.')
    # TODO:
    # 1. Fix cooldown, yield cooldown time and user on try.
    # 2. Clean up code
    @commands.cooldown(1, 1800, type=commands.BucketType.user)
    async def votekick(self, ctx: discord.ext.commands.Context, user: str, time=30):
        author = ctx.message.author
        victim_id = int(user.replace('<', '').replace('@', '').replace('>', '').replace('!', ''))
        victim = await self.bot.fetch_user(user_id=victim_id)

        # check if author is connected to any server, so we can determine, which voice channel to check
        if author.voice is None:
            await ctx.send(f'{author.name} is not connected to any voice channel!')
            return

        # author_msg = ctx.message
        guild = author.guild
        voice_channel = author.voice.channel

        # find KICKED role in server
        # KICKED temporary blocks from joining any voice channels, default time = 10 seconds
        kicked_role = discord.Role
        for role in guild.roles:
            if role.name == 'KICKED':
                kicked_role = role
                break

        # send votekick message
        vote = await ctx.send(f'Vote to kick user: {victim.mention}. Vote author: {author.mention}. '
                              f'\N{THUMBS UP SIGN} for yes, \N{THUMBS DOWN SIGN} for no.')
        # add reactions to vote
        emoji_yes = '\N{THUMBS UP SIGN}'
        emoji_no = '\N{THUMBS DOWN SIGN}'
        await vote.add_reaction(emoji_yes)
        await vote.add_reaction(emoji_no)
        reactions = vote.reactions

        # wait until reactions list is properly refreshed
        while len(reactions) != 2:
            await asyncio.sleep(1)
            vote = await ctx.fetch_message(vote.id)
            reactions = vote.reactions

        # send timer message
        if time < 10:
            time = 20
        timer = await ctx.send(f'{time} seconds left!')

        # iterate through given voice channel
        members = voice_channel.members
        victim_member = discord.Member
        for i in guild.members:
            if i.id == victim.id:
                victim_member = i
                break

        # set vote timer
        while time != 0:
            time -= 1
            await asyncio.sleep(1)
            await timer.edit(content=f'{time} seconds left!')
            members = voice_channel.members
            # if user no longer in given channel, mock and punish him
            if victim_member not in members:
                await ctx.send(f'{victim.mention} fleed!')
                await vote.delete()
                await timer.delete()
                await victim_member.add_roles(kicked_role)
                # block 10 times longer after flee!
                time = 100
                while time != 0:
                    time -= 1
                    await asyncio.sleep(1)
                await victim_member.remove_roles(kicked_role)
                break

        # iterate through channel members
        for i in members:
            # if we find desired victim
            if i.id == victim.id:

                # wait until reactions list is properly refreshed (and has only 2 votes)
                while len(reactions) != 2:
                    await asyncio.sleep(1)
                    vote = await ctx.fetch_message(vote.id)
                    reactions = vote.reactions

                # if anyone has voted
                if reactions[0].count + reactions[1].count > 2:

                    # if yes/no votes ratio is greater than 2/3
                    if (reactions[0].count - 1) / (reactions[0].count + reactions[1].count - 2) >= 2/3:

                        # creates a temp channel to move victim to
                        # then delete it to successfully kick them from the server
                        # also gives KICKED role to victim
                        kick_channel = await guild.create_voice_channel('kick', category=guild.categories[len(guild.categories) - 1])
                        await i.add_roles(kicked_role)
                        await i.move_to(kick_channel)
                        await kick_channel.delete()
                        await vote.edit(content=f'{victim.mention} successfully kicked! '
                                        f'Voted yes: {reactions[0].count - 1} Voted no: {reactions[1].count - 1}')

                    # yes/no is not greater than 2/3 = vote failed
                    else:
                        await vote.edit(content=f'{victim.mention} was not kicked! '
                                                f'Voted yes: {reactions[0].count - 1} Voted no: {reactions[1].count - 1}')
                else:
                    await vote.edit(content=f'No one has voted!')

                # remove reactions
                for reaction in reactions:
                    await reaction.clear()
                await timer.delete()

                # remove KICKED role after x seconds, default time = 10 seconds
                time = 10
                while time != 0:
                    time -= 1
                    await asyncio.sleep(1)
                await i.remove_roles(kicked_role)


def setup(bot):
    bot.add_cog(Vote(bot))
