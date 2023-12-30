import math

import discord
from discord.ui import Button, View
from discord.ext import commands


class Paginator():
    def __init__(
                self, 
                ctx: commands.Context,              # ctx object, used to collect author and text channel
                title: str | list[str] = "",        # embed title
                entries: list = [],                 # list of entries to be added to embed
                colour: int | list[int] = 0,        # embed outline colour
                length: int = 1,                    # number of entries to enter per page
                author_restrict: bool = True,       # True -> only author can use buttons
                timeout: int = 30,                  # navigation button expity (seconds)
                prefix: str = "",                   # prefix to add before each entry
                suffix: str = "",                   # suffix to add after each entry
                init_page: int = 1,                 # page number to open at start
                reply: bool = True,                 # send as message or as a reply. True will send as reply
                linesep = "\n",                     # token used to separate lines
                message = "",                       # extra message sent with embed, on top of embed
                thumbnail: str | list[str] = None   # thumbnail of the embed
                ):
        
        # Every embed page must have atleast one entry
        if length < 1:
            raise ValueError("Length cannot be less than 1")
        
        self.ctx = ctx
        self.title = title
        self.entries = entries
        self.colour = colour
        self.length = length
        self.author_restrict = author_restrict
        self.timeout = timeout
        self.prefix = prefix
        self.suffix = suffix
        self.init_page = init_page
        self.reply = reply
        self.linesep = linesep
        self.message = message
        self.thumbnail = thumbnail
        
        self.current = None         # indicator for embed object
        self.current_page = 1       # indicator for currently viewing page number
        self.pages = []             # list of pages. pages are created by parse pages function
        
        # number of total pages = (total entries / entries per page) rounded up
        self.total_pages = math.ceil(len(self.entries) / self.length)
        
    def parse_pages(self) -> None:
        # simply create a list of lists. each list will then be added its respective content
        self.pages = [[] for i in range(self.total_pages)]
        
        # keeps track of page number
        count = 0
        
        # run this loop until all entries are loaded into pages
        while len(self.entries) > 0:
            # add as many entries into current page as defined in self.length
            # any added entries should be removed from entries list]
            for _ in range(self.length):
                if len(self.entries) > 0:
                    self.pages[count].append(self.entries[0] + self.linesep)
                    self.entries.pop(0)
            count += 1
    
    # create and return the navigation bar for the embed
    async def nav(self) -> View:
        # define buttons
        delete_button = Button(emoji="✖️", style=discord.ButtonStyle.danger)
        first_button = Button(emoji="⏪", style=discord.ButtonStyle.blurple)
        previous_button = Button(emoji="◀️", style=discord.ButtonStyle.blurple)
        next_button = Button(emoji="▶️", style=discord.ButtonStyle.blurple)
        last_button = Button(emoji="⏩", style=discord.ButtonStyle.blurple)
        
        # define callbacks for each button
        async def delete_callback(interaction):
            await self.delete()                             # delete embed
            await interaction.response.defer()
        
        async def first_callback(interaction):
            self.current_page = 1                           # go to page number 1
            await self.update()
            await interaction.response.defer()
        
        async def previous_callback(interaction):
            if self.current_page-1 < 0:
                return
            self.current_page -= 1                          # go to previous page (current page -1)
            await self.update()
            await interaction.response.defer()
            
        async def next_callback(interaction):
            if self.current_page+1 > len(self.pages):
                return
            self.current_page += 1                          # go to next page (current page +1)
            await self.update()
            await interaction.response.defer()
            
        async def last_callback(interaction):
            self.current_page = self.total_pages            # go to last page (last page index is also equal to total page count)
            await self.update()
            await interaction.response.defer()
            
            
        #assign callbacks
        delete_button.callback = delete_callback
        first_button.callback = first_callback
        previous_button.callback = previous_callback
        next_button.callback = next_callback
        last_button.callback = last_callback
        
        # add all buttons to view
        view = View()
        view.add_item(delete_button)
        view.add_item(first_button)
        view.add_item(previous_button)
        view.add_item(next_button)
        view.add_item(last_button)
        
        return view
            
    # send the embed and initiate buttons
    async def start(self) -> None:
        if isinstance(self.title, str):
            title = self.title
        else:
            title = self.title[self.init_page-1]
            
        if isinstance(self.colour, int):
            colour = self.colour
        else:
            colour = self.colour[self.init_page-1]
        
        embed = discord.Embed(
            title = title,
            description = "",
            colour = colour
        )
        
        self.parse_pages()
        
        # for every entry in the first page, add the entry to description with prefix and suffix
        for entry in self.pages[self.init_page-1]:
            embed.description += f"{self.prefix}{entry}{self.suffix}"
        
        # only add footer with page numbers and navigation if there exists more than 1 page
        if self.total_pages > 1:
            embed.set_footer(text=f"Page {self.init_page} of {self.total_pages}")
            view = await self.nav()
        else:
            view = None
        
        if self.thumbnail:
            if isinstance(self.thumbnail, str):
                embed.set_thumbnail(url=self.thumbnail)
            else:
                embed.set_thumbnail(url=self.thumbnail[self.init_page-1])
            
        # if set to reply mode, send message as reply, otherwise simply send to channel
        if self.reply:
            self.current = await self.ctx.reply(self.message, embed=embed, view=view)
        else:
            self.current = await self.ctx.send(self.message, embed=embed, view=view)
            
    # update embed every time new page is requested
    async def update(self) -> None:
        if isinstance(self.title, str):
            title = self.title
        else:
            title = self.title[self.current_page - 1]
            
        if isinstance(self.colour, int):
            colour = self.colour
        else:
            colour = self.colour[self.current_page - 1]
        
        embed = discord.Embed(
            title = title,
            description = "",
            colour = colour
        )
        
        if self.thumbnail:
            if isinstance(self.thumbnail, str):
                embed.set_thumbnail(url=self.thumbnail)
            else:
                embed.set_thumbnail(url=self.thumbnail[self.current_page-1])
        
        # iterate through each entry in current page and append to description with prefix and suffix
        for entry in self.pages[self.current_page-1]:
            embed.description += f"{self.prefix}{entry}{self.suffix}"
            
        embed.set_footer(text=f"Page {self.current_page} of {self.total_pages}")
        
        await self.current.edit(content=self.message, embed=embed, view=await self.nav())
        
    # delete embed
    async def delete(self) -> None:
        await self.current.delete()
        
    async def close_page(self) -> None:
        await self.delete()
        
    async def clear(self) -> None:
        self.pages = []
            