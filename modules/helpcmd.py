import discord
from discord.ext import commands

from modules import jsonhandler
from modules.paginator import Paginator


async def get_command_signature(command: commands.Command, ctx: commands.Context):
    try:
        command_invoke = f"[{command.name}|{'|'.join(command.aliases)}]" if command.aliases else command.name
    except AttributeError:
        command_invoke = command.name
    full_invoke = command.qualified_name.replace(command.name, "")
    try:
        return f"/{full_invoke}{command_invoke} {command.signature}"
    except AttributeError:
        return f"/{full_invoke}{command_invoke}"

async def get_app_command_signature(command: discord.app_commands.Command, ctx: commands.Context):
    full_invoke = command.qualified_name.replace(command.name, "")
    try:
        return f"/{full_invoke}{command.name} | parameters: {' '.join(param.name for param in command.parameters)}" if command.parameters else f"/{full_invoke}{command.name}"
    except AttributeError:
        return f"/{full_invoke}{command.name}"

async def get_command_group_signature(command: commands.HybridGroup, ctx: commands.Context):
    try:
        command_invoke = f"[{command.name}|{'|'.join(command.aliases)}]" if command.aliases else command.name
    except AttributeError:
        command_invoke = command.name
    full_invoke = command.qualified_name.replace(command.name, "")
    return f"/{full_invoke}{command_invoke}"

async def sort_commands( commandList: list) -> list:
    return sorted(commandList, key=lambda x: x.name)

async def filter_commands(walkable: commands.Cog, ctx: commands.Context) -> list:
    try:
        filtered = [command for command in walkable.get_app_commands()]
    except AttributeError:
        filtered = []
    
    # ToDo: This does not read app commands. Fix it
    
    for command in walkable.walk_commands():
        try:
            try:
                if command.hidden:
                    continue
            except AttributeError:
                pass
            # uncomment to exclude all subcommands from main help command
            # if command.parent:
            #     continue
            try:
                await command.can_run(ctx)
            except AttributeError:
                pass
            filtered.append(command)
            
        except commands.CommandError:
            continue
        
    return await sort_commands(filtered)
    
    
async def setup_help_page(client: commands.Bot, ctx: commands.Context, entity: str = None, title: str = None, commands_per_page: int = 15, is_error=False, error: str = "") -> None:
    entity = entity or client
    if is_error:
        error = "\n".join(error[:3])
        error = f"Incorrect usage for {title}\n{error}"
        title = f"{title} usage"
    else:
        title = title or client.description
        
    entries = []
    
    if isinstance(entity, (commands.Command, discord.app_commands.Command)):
        # get all subcommands if the command has subcommands, otherwise empty list
        filtered_commands = list(set(entity.all_commands.values())) if hasattr(entity, "all_commands") else []
        filtered_commands.insert(0, entity) # add parent command to start of list
    elif isinstance(entity, (commands.Cog, commands.HybridGroup, commands.Group, discord.app_commands.commands.Group)):
        filtered_commands = await filter_commands(entity, ctx)
    else:
        filtered_commands = {}
        for cog in entity.cogs:
            filtered_commands[cog] = await filter_commands(entity.get_cog(cog), ctx)
        
    if isinstance(entity, (commands.Cog, commands.Command, discord.app_commands.Command, commands.HybridGroup, commands.Group, discord.app_commands.commands.Group)):
        if isinstance(entity, (commands.HybridGroup, commands.Group, commands.hybrid.HybridAppCommand)) or type(filtered_commands[0]) == commands.hybrid.HybridAppCommand:
            desc = entity.description or entity.short_doc
            desc = "\n" + desc
            signature = await get_command_group_signature(entity, ctx)
            commands_entry = (f"• **__{entity.name}__**\n```\n{signature}\n```{desc}")
            entries.append("\u200b\n" + commands_entry)
            
        for command in filtered_commands:
            desc = command.description or command.short_doc
            desc = "\n" + desc
            if isinstance(command, (commands.Command)):
                signature = await get_command_signature(command, ctx)
            else:
                signature = await get_app_command_signature(command, ctx)
            subcommand = "\nHas subcommands" if hasattr(command, "all_commands") else ""
            
            if not command.parent:
                commands_entry = (
                    f"• **__{command.name}__**\n```\n{signature}\n```{desc}"
                    if isinstance(entity, (commands.Command, commands.HybridCommand, discord.app_commands.Command, commands.HybridCommand, commands.HybridGroup, commands.Group, discord.app_commands.commands.Group))
                    else f"• **__{command.name}__**{desc}{subcommand}"
                    )
            else:
                commands_entry = (
                    f"• **__{command.parent.name} {command.name}__**\n```\n{signature}\n```{desc}"
                    if isinstance(entity, (commands.Command, commands.HybridCommand, discord.app_commands.Command, commands.HybridCommand, commands.HybridGroup, commands.Group, discord.app_commands.commands.Group))
                    else f"• **__{command.parent.name} {command.name}__**{desc}{subcommand}"
                    )
            
            entries.append("\u200b\n" + commands_entry)
        
    else:
        for cog, commands_page in filtered_commands.items():
            if not commands_page:
                continue
            entries.append(f"\u200b\n**{cog}**:\n{''.join([f'`{command.name}` ' for command in commands_page])}")
            entries.sort()
            
    try:
        avatar = client.user.avatar.url
    except AttributeError:
        avatar = None
        
    await Paginator(
        ctx=ctx,
        entries=entries,
        title=title,
        colour=jsonhandler.fetch_data("orange", "colours"),
        length=commands_per_page,
        timeout=30,
        message=error,
        thumbnail=avatar
    ).start()

async def initiate_helpcmd(client: commands.Bot, ctx: commands.Context, entity: str, is_error=False, error: str = None) -> None:
    if not entity:
        await setup_help_page(client, ctx, is_error=is_error, error=error, commands_per_page=10)
    else:
        command = client.tree.get_command(entity)
        if not command:
            command = client.get_command(entity)
        if not command:
            entitylist = entity.split()
            command = client.tree.get_command(entitylist[0])
            if command:
                command = command.get_command(entitylist[1])
        if command:
            await setup_help_page(client, ctx, command, command.name, is_error=is_error, error=error, commands_per_page=10)
        else:
            cog = client.get_cog(entity)
            if cog:
                await setup_help_page(client, ctx, cog, f"{cog.qualified_name} commands", is_error=is_error, error=error, commands_per_page=10)
            else:
                await ctx.reply("Entity Not Found")
