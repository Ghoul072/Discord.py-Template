import contextlib
import io
import os
import textwrap
from traceback import format_exception

import discord
from discord.ext import commands

from modules import jsonhandler
from modules.paginator import Paginator


# Heart Cog. The heart of the bot and includes all vital commands for proper functionality. All commands in this cog are hidden
class Heart(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
    
    # remove backticks from code for eval command
    @staticmethod
    def clean_code(code: str) -> str:
        if code.startswith("```") and code.endswith("```"):
            return "\n".join(code.split("\n")[1:])[:-3]
        else:
            return code
        
    # return True if a given cog name exists within cog directory
    @staticmethod
    async def cog_exists(extension: str) -> bool:
        for pyfile in os.listdir("./cogs"):
            if pyfile == f"{extension}.py":
                return True
        else:
            return False

    # sync command tree. only usable by bot owners
    @commands.is_owner() 
    @commands.command(name="sync", help="Sync slash commands", hidden=True)
    async def sync(self, ctx: commands.Context) -> None:
        await ctx.reply("Attempting to sync commands")
        try:
            await self.client.tree.sync()
        except Exception as error:
            await ctx.reply("Error when attempting to sync commands")
            raise error
        else:
            await ctx.reply("Slash commands synced successfully")
    
    # execute python code. only usable by bot owners
    @commands.is_owner()
    @commands.command(name="eval", aliases=["execute", "exec"], help="Run python code", hidden=True)
    async def execute_code(self, ctx: commands.Context, *, code: str) -> None:
        """
        :param code: Block of code to run
        :type code: str
        """
        if not code:
            await ctx.reply("No command given")
            return
        
        code = self.clean_code(code)
        
        # define local variables for ease of use
        local_variables = {
        "discord": discord,
        "commands": commands,
        "bot": self.client,
        "client": self.client,
        "ctx": ctx,
        "message": ctx.message,
        "author": ctx.author,
        "channel": ctx.channel,
        "guild": ctx.guild
        }
        
        # output set to StringIO object
        stdout = io.StringIO()
        
        try:
            # redirect output to stringIO
            with contextlib.redirect_stdout(stdout):
                
                # execute block
                exec(f"async def function():\n{textwrap.indent(code, '    ')}", local_variables)
                
                # format result as (printed lines \n -- returned lines), embed title is SUCCESS
                obj = await local_variables["function"]()
                result = f"{stdout.getvalue()}\n-- {obj}"
                title = "**SUCCESS**"
                colour = jsonhandler.fetch_data("orange", "colours")
                
        # if error, send error as the result itself
        except Exception as error:
            result = "".join(format_exception(error, error, error.__traceback__))
            title = "**ERROR**"
            colour = jsonhandler.fetch_data("red", "colours")
            
        # send all output as a paged embed
        pager = Paginator(
            timeout=100,
            title=title,
            ctx=ctx,
            entries=[result[i: i + 2000] for i in range(0, len(result), 2000)],
            colour=colour,
            length=1,
            prefix="```\n",
            suffix="\n```"
        )
        await pager.start()
    
    # load a cog/extension  
    @commands.is_owner()
    @commands.command(name="load", help="Load extension/cog", hidden=True)
    async def load_cog(self, ctx: commands.Context, *, extension: str) -> None:
        """
        :param extension: Name of extension to load
        :type extension: str
        """
        if extension == "all":
            output = ""
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    filename = filename[:-3] # remove .py from ending
                    try:
                        await self.load_extension(f"cogs.{filename}")
                    except commands.ExtensionFailed as error:
                        output += f"\n{error}"
                    except commands.NoEntryPointError as error:
                        output += f"\nPy file is not a cog: {filename}"
                    else:
                        output += f"\nSuccessfully loaded {filename} cog"
            await ctx.reply(output)
            return
        
        filename, cog_title = extension.lower(), extension.title()
        
        try:
            await self.client.load_extension(f"cogs.{filename}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.reply(f"Cog \"{cog_title}\" is already loaded")
        except commands.ExtensionNotFound:
            await ctx.reply(f"\"{cog_title}\" not found")
        except:
            await ctx.reply(f"Error inside Cog \"{cog_title}\". This cog needs to be fixed before it can be used")
        else:
            await ctx.reply(f"Successfully loaded cog \"{cog_title}\"")
    
    # unload a cog/extension        
    @commands.is_owner()
    @commands.command(name="unload", help="Unload extension/cog", hidden=True)
    async def unload_cog(self, ctx: commands.Context, *, extension: str) -> None:
        """
        :param extension: Name of extension to unload
        :type extension: str
        """
        filename, cog_title = extension.lower(), extension.title()
        
        if filename == "heart":
            await ctx.reply("WARNING: Unloading my heart means you can no longer access my vital commands, including commands sync, cog load/unload and eval commands\n"
                           f"Use command {ctx.prefix}heart to load heart cog")
        
        # "cog not found" if cog does not exist. "cog not loaded" if cog exists but not loaded
        try:
            await self.client.unload_extension(f"cogs.{filename}")
        except commands.ExtensionNotLoaded:
            if await self.cog_exists(filename):
                await ctx.reply(f"Cog \"{cog_title}\" not loaded")
            else:
                await ctx.reply(f"Cog \"{cog_title}\" not found")
        else:
            await ctx.reply(f"Successfully unloaded cog \"{cog_title}\"")
                
    # reload an already loaded cog/extension
    @commands.is_owner()
    @commands.command(name="reload", help="Reload extension/cog", hidden=True)
    async def reload_cog(self, ctx: commands.Context, *, extension: str) -> None:
        """
        :param extension: Name of extension to reload
        :type extension: str
        """
        filename, cog_title = extension.lower(), extension.title()
        
        if filename == "heart":
            await ctx.reply("WARNING: Unloading my heart means you can no longer access my vital commands, including commands sync, cog load/unload and eval commands\n"
                           f"Use command {ctx.prefix}heart to load heart cog in case any errors occur")
        
        # attempt to unload cog, if successful, reload the respective cog
        try:
            await self.client.unload_extension(f"cogs.{filename}")
        except commands.ExtensionNotLoaded:
            if await self.cog_exists(filename):
                await ctx.reply(f"Cog \"{cog_title}\" not loaded")
            else:
                await ctx.reply(f"Cog \"{cog_title}\" not found")
        else:
            try:
                await self.client.load_extension(f"cogs.{filename}")
            except commands.ExtensionNotFound:
                await ctx.reply(f"Cog \"{cog_title}\" is no longer available. Unloaded successfully")
            except Exception as error:
                await ctx.reply(f"Error inside Cog \"{cog_title}\". This cog needs to be fixed before it can be used again")
                raise error
            else:
                await ctx.reply(f"Successfully reloaded cog \"{cog_title}\"")
                
        
    @commands.command(name="cogs", help="Display all cogs/extensions", hidden=True)
    async def display_cogs(self, ctx: commands.Context) -> None:
        cogs = self.client.cogs
        if len(cogs) < 1:
            await ctx.reply("No loaded cogs")
            return
        embed = Paginator (
            ctx=ctx,
            title="**Cogs**",
            entries=sorted([cog for cog in cogs]),
            colour=jsonhandler.fetch_data("orange", "colours"),
            length=10,
        )
        await embed.start()
    

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Heart(client))
