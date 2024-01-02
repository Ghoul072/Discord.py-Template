import discord
from discord.ext import commands
from discord import app_commands
from modules import jsonhandler


# Cog for all miscellaneous commands 
class Misc(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        
    # latency checker
    @app_commands.command(name="ping", description="Return latency of the bot")
    async def latency(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
        embed=discord.Embed(
            title = "**LATENCY**",
            colour = jsonhandler.fetch_data("blue", "colours"),
            description = f"{round(self.client.latency*1000)} ms"
        )
    )
        
    # say a certain line of text
    @app_commands.command(name="say", description="Repeat a line of text")
    async def repeat_text(self, interaction: discord.Interaction, text: str) -> None:
        """
        :param text: Repeat/Quote a line of text
        :type text: str
        """
        if await self.client.is_owner(interaction.user):
            await interaction.response.send_message("ok", ephemeral=True, delete_after=0.5)
            
        if await self.client.is_owner(interaction.user):
            await interaction.channel.send(text)
        else:
            await interaction.channel.send(f"\"{text}\"\n-{interaction.user.nick or interaction.user.name}")
            
    @app_commands.command(name="avatar", description="Get profile picture of yourself or someone else")
    async def get_avatar(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        """
        :param member: User to get the avatar of, defaults to author who used the command
        :type member: discord.Member, optional
        """
        if not member:
            member = interaction.user
        await interaction.response.send_message(member.avatar)
        
    @app_commands.command(name="impersonate", description="Impersonate a user or bot and send a message as the member")
    async def impersonate_member(self, interaction: discord.Interaction, member: discord.Member, *, message: str) -> None:
        """
        :param member: Member or Bot account to impersonate
        :type member: discord.Member
        :param message: Message to send as the member
        :type message: str
        """
        if await self.client.is_owner(interaction.user):
            await interaction.response.send_message("ok", ephemeral=True, delete_after=0.5)
        webhook = await interaction.channel.create_webhook(name=member.name + member.discriminator)
        if not message:
            message = ""
        await webhook.send(message, username=member.display_name, avatar_url=member.avatar.url)
        await webhook.delete()
        
    @commands.is_owner()
    @commands.command(name="status", description="Change my status")
    async def change_status(self, ctx: commands.Context, status: str, *, message: str = None) -> None:
        """
        :param status: Status to change to
        :type status: str
        """

        if status == "online":
            status = discord.Status.online
        elif status == "idle":
            status = discord.Status.idle
        elif status == "dnd":
            status = discord.Status.dnd
        elif status == "invisible":
            status = discord.Status.invisible
        else:
            return await ctx.reply(f"Invalid status: **'{status}'**. Available statuses are online, idle, dnd and invisible")
        
        if message:
            await self.client.change_presence(status=status, activity=discord.Game(name=message))
            return await ctx.reply(f"Successfully changed status to **{status}** with message: **{message}**")
        else:
            await self.client.change_presence(status=status)
            return await ctx.reply(f"Successfully changed status to {status}")   
    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Misc(client))
