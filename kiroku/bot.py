import logging
import os
import typing

from hikari import (
    Activity,
    ActivityType,
    Intents,
    StartedEvent,
    StartingEvent,
    StoppingEvent,
)
from hikari.impl.config import CacheSettings
from lightbulb import BotApp
import miru

from kiroku.util.file import Paths

from kiroku import SYSLOG, __version__, __version_tuple__
from kiroku.store import Store

print(__name__)

BOT_PREFIX = ">"

Store.configs = {}
Store.indev = bool(os.getenv("DEV"))
Store.extensions_dict = {}
Store.logs = {}


syslog = logging.getLogger(SYSLOG)

KBotT = typing.TypeVar("KBotT", bound="KBot")


def autoload_extensions(kbot: KBotT) -> bool:
    """Find and load extensions"""
    ext_first = []
    ext_last = []
    for ext in Paths.exts.iterdir():
        if ext.name.startswith("_") or not ext.suffix.endswith("py"):
            continue
        elif ext.name.startswith("bot"):
            # extensions prefixed with 'bot' must load last
            ext_last.append(ext)
        else:
            ext_first.append(ext)
    ok = True
    for ext in ext_first + ext_last:
        syslog.debug(f"Autoloading: {ext.name}")
        ext_dot = f"{Paths.project.name}.{Paths.exts.name}.{ext.stem}"
        Store.extensions_dict[ext.stem] = ext_dot
        try:
            kbot.load_extensions(ext_dot)
        except Exception:
            ok = False
            syslog.exception("Autoload Extension Failed: %s", ext)
    return ok


class KBot(BotApp):
    """bot"""

    def __init__(self) -> None:
        """innit mate"""
        token = os.getenv("DISTOKEN")
        super().__init__(
            token=token,
            intents=Intents.ALL_UNPRIVILEGED
            | Intents.MESSAGE_CONTENT
            | Intents.GUILD_MEMBERS,
            prefix=BOT_PREFIX,
            cache_settings=CacheSettings(max_messages=5_000, max_dm_channel_ids=250),
        )

    def run(self: KBotT) -> None:
        """runnit mate"""
        syslog.info("indev %s | %s | %s", Store.indev, __version__, self.cache.settings)

        self.event_manager.subscribe(StartingEvent, self.before_ready)
        self.event_manager.subscribe(StartedEvent, self.on_ready)
        self.event_manager.subscribe(StoppingEvent, self.on_close)

        ver = f"{__version_tuple__[0]}.{__version_tuple__[1]}"
        if Store.indev:
            act = Activity(
                name="testing | " + ver,
                type=ActivityType.COMPETING,
            )
        else:
            act = Activity(
                name=f"to {BOT_PREFIX} and / | {ver}",
                type=ActivityType.LISTENING,
            )

        super().run(activity=act)

    async def before_ready(self: KBotT, event: StartingEvent):  # noqa: D401
        """Fired before bot is ready"""
        syslog.debug("before_ready")
        miru.install(self)
        autoload_extensions(self)

    async def on_ready(self: KBotT, event: StartedEvent):  # noqa: D401
        """Fired when bot is ready"""
        syslog.debug("on_ready")

    async def on_close(self: KBotT, event: StoppingEvent):  # noqa: D401
        """Fired when bot is stopping"""
        syslog.critical("on_close")


# MIT APasz
