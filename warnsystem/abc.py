from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redbot.core import Config, commands
    from redbot.core.bot import Red
    from .api import API


class MixinMeta(ABC):
    """
    Base class for well behaved type hint detection with composite class.

    Basically, to keep developers sane when not all attributes are defined in each mixin.

    Credit to https://github.com/Cog-Creators/Red-DiscordBot (mod cog) for all mixin stuff.
    """

    def __init__(self, *_args):
        self.bot: Red
        self.data: Config
        self.api: API
