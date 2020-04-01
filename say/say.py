# Say by retke, aka El Laggron

import discord
import asyncio
import os
import logging

from datetime import datetime
from typing import Optional, Union

from redbot.core.bot import Red
from redbot.core import checks, commands
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.common_filters import filter_mass_mentions
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.tunnel import Tunnel

from .utils import _check_owner, _str_to_json

log = logging.getLogger("laggron.say")
log.setLevel(logging.DEBUG)

_ = Translator("Say", __file__)


@cog_i18n(_)
class Say(commands.Cog):
    """
    Speak as if you were the bot

    Report a bug or ask a question: https://discord.gg/AVzjfpR
    Full documentation and FAQ: http://laggrons-dumb-cogs.readthedocs.io/say.html
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.interaction = []
        self._init_logger()

    __author__ = ["retke (El Laggron)", "Predä"]
    __version__ = "1.5.0"

    def _init_logger(self):
        log_format = logging.Formatter(
            f"%(asctime)s %(levelname)s {self.__class__.__name__}: %(message)s",
            datefmt="[%d/%m/%Y %H:%M]",
        )
        # logging to a log file
        # file is automatically created by the module, if the parent foler exists
        cog_path = cog_data_path(self)
        if cog_path.exists():
            log_path = cog_path / f"{os.path.basename(__file__)[:-3]}.log"
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(log_format)
            log.addHandler(file_handler)

        # stdout stuff
        stdout_handler = logging.StreamHandler()
        stdout_handler.setFormatter(log_format)
        # if --debug flag is passed, we also set our debugger on debug mode
        if logging.getLogger("red").isEnabledFor(logging.DEBUG):
            stdout_handler.setLevel(logging.DEBUG)
        else:
            stdout_handler.setLevel(logging.INFO)
        log.addHandler(stdout_handler)
        self.stdout_handler = stdout_handler

    async def say(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel],
        payload: Union[str, dict],
        files: list,
    ):
        if not channel:
            channel = ctx.channel
        if not payload and not files:
            await ctx.send_help()
            return

        # preparing context info in case of an error
        if files != []:
            error_message = (
                "Has files: yes\n"
                f"Number of files: {len(files)}\n"
                f"Files URL: " + ", ".join([x.url for x in ctx.message.attachments])
            )
        else:
            error_message = "Has files: no"

        # sending the message
        try:
            if isinstance(payload, dict):
                if not _check_owner(ctx) and payload.get("content"):
                    payload["content"] = filter_mass_mentions(payload["content"])
                if payload.get("embed"):
                    if payload["embed"].get("timestamp"):
                        payload["embed"]["timestamp"] = None  # TODO: Handle this.
                    payload["embed"] = discord.Embed.from_dict(payload["embed"])
                try:
                    await channel.send(**payload)
                except TypeError:
                    await ctx.send(_("Something is wrong in your JSON input."))
            else:
                if _check_owner(ctx):
                    await channel.send(payload, files=files)
                else:
                    await channel.send(filter_mass_mentions(payload), files=files)
        except discord.errors.HTTPException as e:
            if not ctx.guild.me.permissions_in(channel).send_messages:
                author = ctx.author
                try:
                    await ctx.send(
                        _("I am not allowed to send messages in ") + channel.mention,
                        delete_after=2,
                    )
                except discord.errors.Forbidden:
                    await author.send(
                        _("I am not allowed to send messages in ") + channel.mention,
                        delete_after=15,
                    )
                    # If this fails then fuck the command author
            elif not ctx.guild.me.permissions_in(channel).attach_files:
                try:
                    await ctx.send(
                        _("I am not allowed to upload files in ") + channel.mention, delete_after=2
                    )
                except discord.errors.Forbidden:
                    await author.send(
                        _("I am not allowed to upload files in ") + channel.mention,
                        delete_after=15,
                    )
            elif e.code == 50035:
                await ctx.send(e.text)
            else:
                log.error(
                    f"Unknown permissions error when sending a message.\n{error_message}",
                    exc_info=e,
                )

    @commands.command(name="say")
    async def _say(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel], *, text: str = ""
    ):
        """
        Make the bot say what you want in the desired channel.

        If no channel is specified, the message will be send in the current channel.
        You can attach some files to upload them to Discord.

        Example usage :
        - `[p]say #general hello there`
        - `[p]say owo I have a file` (a file is attached to the command message)
        """

        files = await Tunnel.files_from_attatch(ctx.message)
        await self.say(ctx, channel, text, files)

    @commands.command(name="sayembed", aliases=["sayem"])
    async def _sayembed(self, ctx: commands.Context, *, json: str = None):
        """
        Make the bot say what you want in an embed in the current channel.

        You need to send a valid JSON, that you can made from here: https://leovoel.github.io/embed-visualizer/
        Example usage:
        - `[p]sayembed {"embed": {"title": "Hey a blue embeded message!", "color": 431075}}`
        - `[p]sayembed {"content": "A message above this embed!", "embed": {"title": "And a blue embeded message!", "color": 431075}}`
        """

        if not json:
            return await ctx.send_help()
        files = await Tunnel.files_from_attatch(ctx.message)
        data = await _str_to_json(json)
        if not data:
            return await ctx.send(_("This is not a valid JSON."))
        await self.say(ctx, None, data, files)

    @commands.command(name="sayd", aliases=["sd"])
    async def _saydelete(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel], *, text: str = ""
    ):
        """
        Same as say command, except it deletes your message.

        If the message wasn't removed, then I don't have enough permissions.
        """

        # download the files BEFORE deleting the message
        author = ctx.author
        files = await Tunnel.files_from_attatch(ctx.message)

        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            try:
                await ctx.send(_("Not enough permissions to delete messages."), delete_after=2)
            except discord.errors.Forbidden:
                await author.send(_("Not enough permissions to delete messages."), delete_after=15)

        await self.say(ctx, channel, text, files)

    @commands.command(name="interact")
    async def _interact(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Start receiving and sending messages as the bot through DM"""

        u = ctx.author
        if channel is None:
            if isinstance(ctx.channel, discord.DMChannel):
                await ctx.send(
                    _(
                        "You need to give a channel to enable this in DM. You can "
                        "give the channel ID too."
                    )
                )
                return
            else:
                channel = ctx.channel

        if u in self.interaction:
            await ctx.send(_("A session is already running."))
            return

        message = await u.send(
            _(
                "I will start sending you messages from {0}.\n"
                "Just send me any message and I will send it in that channel.\n"
                "React with ❌ on this message to end the session.\n"
                "If no message was send or received in the last 5 minutes, "
                "the request will time out and stop."
            ).format(channel.mention)
        )
        await message.add_reaction("❌")
        self.interaction.append(u)

        while True:

            if u not in self.interaction:
                return

            try:
                message = await self.bot.wait_for("message", timeout=300)
            except asyncio.TimeoutError:
                await u.send(_("Request timed out. Session closed"))
                self.interaction.remove(u)
                return

            if message.author == u and isinstance(message.channel, discord.DMChannel):
                files = await Tunnel.files_from_attatch(message)
                await channel.send(message.content, files=files)
            elif (
                message.channel != channel
                or message.author == channel.guild.me
                or message.author == u
            ):
                pass

            else:
                embed = discord.Embed()
                embed.set_author(
                    name="{} | {}".format(str(message.author), message.author.id),
                    icon_url=message.author.avatar_url,
                )
                embed.set_footer(text=message.created_at.strftime("%d %b %Y %H:%M"))
                embed.description = message.content
                embed.colour = message.author.color

                if message.attachments != []:
                    embed.set_image(url=message.attachments[0].url)

                await u.send(embed=embed)

    @commands.command(hidden=True)
    @checks.is_owner()
    async def sayinfo(self, ctx: commands.Context):
        """
        Get informations about the cog.
        """
        await ctx.send(
            _(
                "Laggron's Dumb Cogs V3 - say\n\n"
                "Version: {0.__version__}\n"
                "Author: {0.__author__}\n"
                "Github repository: https://github.com/retke/Laggrons-Dumb-Cogs/tree/v3\n"
                "Discord server: https://discord.gg/AVzjfpR\n"
                "Documentation: http://laggrons-dumb-cogs.readthedocs.io/\n\n"
                "Support my work on Patreon: https://www.patreon.com/retke"
            ).format(self)
        )

    @commands.Cog.listener()
    async def on_reaction_add(
        self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]
    ):
        if user in self.interaction:
            channel = reaction.message.channel
            if isinstance(channel, discord.DMChannel):
                await self.stop_interaction(user)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if not isinstance(error, commands.CommandInvokeError):
            return
        if not ctx.command.cog_name == self.__class__.__name__:
            # That error doesn't belong to the cog
            return
        log.removeHandler(self.stdout_handler)  # remove console output since red also handle this
        log.error(
            f"Exception in command '{ctx.command.qualified_name}'.\n\n", exc_info=error.original
        )
        log.addHandler(self.stdout_handler)  # re-enable console output for warnings

    async def stop_interaction(self, user: Union[discord.Member, discord.User]):
        self.interaction.remove(user)
        await user.send(_("Session closed"))

    def cog_unload(self):
        log.debug("Unloading cog...")
        for user in self.interaction:
            self.bot.loop.create_task(self.stop_interaction(user))
        log.handlers = []
