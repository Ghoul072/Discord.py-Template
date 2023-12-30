import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from modules import jsonhandler
from modules.helpcmd import initiate_helpcmd

load_dotenv()

# main bot object
class Bot(commands.Bot):
    def __init__(
        self, 
        intents=discord.Intents.default(), 
        case_insensitive=True,
        command_prefix=commands.when_mentioned_or(jsonhandler.fetch_data("init_prefix", "config")),
        *args,
        **kwargs
        ):
        super().__init__(
            intents = intents,
            case_insensitive = case_insensitive,
            command_prefix = command_prefix,
            *args,
            **kwargs
        )
        
        # set to True if giving frequent reboots to avoid ratelimiting
        self.synced = True
        
    async def sync_commands(self) -> None:
        """Sync Command Tree"""
        await self.tree.sync()
        print("Slash commands synced successfully")
        
    async def setup_hook(self) -> None:
        """All required setups on start"""
        
        # for all files in cogs directory, try to load as extension if it is a python file
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                filename = filename[:-3] # remove .py from ending
                try:
                    await self.load_extension(f"cogs.{filename}")
                except commands.ExtensionFailed as error:
                    print(error)
                except commands.NoEntryPointError:
                    print(f"Py file is not a cog: {filename}")
                else:
                    print(f"Successfully loaded {filename} cog")
                    
        # sync slash commands on start, does not run if self.synced = True, use feature for testing
        if not self.synced:
            await self.sync_commands()
            
    async def on_ready(self) -> None:
        """Configurations to run when bot is ready"""
        await self.wait_until_ready()
        
        # change bot presence. can be changed as required
        await self.change_presence(status = discord.Status.online)
        
        # bot description
        self.description = f"{self.user.name}: Ghoul's Personal Assistant"
        
        print(f"{self.user} is up and running")
        
        
# create client object
client = Bot(intents=discord.Intents.all())


# backup for loading heart cog in case cog fails
@commands.is_owner()
@client.command(name="heart", help="Load heart cog", hidden=True)
async def load_heart(ctx) -> None:
    """Loads Heart Cog"""
    try:
        await client.load_extension("cogs.heart")
    except commands.ExtensionAlreadyLoaded:
        await ctx.reply("Heart cog already loaded and functional")
    except:
        await ctx.reply("Error inside Heart cog. This needs to be fixed urgently")
    else:
        await ctx.reply("Heart cog is now loaded and functional")
        
        
@client.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    """Exception Handler. Not working for app commands. Test this"""
    
    send_help = (commands.MissingRequiredArgument, commands.BadArgument, commands.TooManyArguments, commands.UserInputError)
    
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("This command is restricted to certain members")

    elif isinstance(error, commands.NotOwner):
        await ctx.reply("This command is owner restricted")
        
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.reply(f"I'm missing some required permissions: {error.missing_permissions}")
        
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.reply(error.original)
        # await ctx.reply(error) # send full error for debugging
        
    elif isinstance(error, send_help):
        name = ctx.command.parent.name + " " + ctx.command.name if ctx.command.parent else ctx.command.name
        await initiate_helpcmd(client=client, ctx=ctx, entity=name, is_error=True, error=error.args)

    else:
        await ctx.reply(error)
        raise error
    
# run client
def run():
    client.run(os.getenv("DISCORD"))
    
    
if __name__ == "__main__":
    run()
