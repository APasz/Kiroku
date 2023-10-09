import logging
import time

from hikari.events import GuildMessageCreateEvent, GuildMessageUpdateEvent

import lightbulb

from .. import SYSLOG
from ..util.message import nice_message, get_logger


print(__name__)
syslog = logging.getLogger(SYSLOG)

plugin = lightbulb.Plugin(name="Event", description="Module housing event functions")

load_time = time.time()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
    global load_time
    load_time = time.time()


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)


def log_message(mess: nice_message, chan_name: str, guild_name: str):
    """Transform event to log"""
    log = get_logger(mess=mess, chan_name=chan_name, guild_name=guild_name)
    log.info(mess.stringise())


# Message Events


def event_log(event):
    """shortcut func"""
    nm = nice_message(mess_obj=event.message, memb_obj=event.get_member())
    cn = event.get_channel().name
    gn = event.get_guild().name
    log_message(mess=nm, chan_name=cn, guild_name=gn)


@plugin.listener(GuildMessageCreateEvent)
async def mesc(event: GuildMessageCreateEvent):
    syslog.debug("message create event")
    event_log(event)


@plugin.listener(GuildMessageUpdateEvent)
async def mesu(event: GuildMessageUpdateEvent):
    syslog.debug("message update event")
    event_log(event)


# MIT APasz
