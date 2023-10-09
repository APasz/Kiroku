import logging
import time
import hikari

import lightbulb
from datetime import datetime
from pathlib import Path as Pathy
import os
import shutil

from kiroku.util.message import nice_message

from .. import SYSLOG, DATE_FORMAT
from ..util.file import Read_Write, Paths

print(__name__)
syslog = logging.getLogger(SYSLOG)

plugin = lightbulb.Plugin(
    name="Command", description="Module housing command functions"
)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)


def get_time() -> str:
    """Get current time in nice format"""
    return datetime.now().strftime(DATE_FORMAT).strip()


@plugin.command
@lightbulb.command("get", "Get message logs")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def get(ctx: lightbulb.Context):
    syslog.warning(
        f"Message logs for {ctx.guild_id} requested by {ctx.author.username} ({ctx.author.id})"
    )

    guild = ctx.get_guild()
    name = f"{guild.name}_({guild.id})"
    guild_folder: Pathy = Paths.logs.joinpath(name)
    zipfile: Pathy = Paths.data.joinpath(f"{name}_{get_time()}.zip")

    if zipfile.exists():
        os.remove(zipfile)
    zipfile = shutil.make_archive(zipfile.stem, "zip", guild_folder)

    await ctx.respond("Message archive", attachment=zipfile)


@plugin.command
@lightbulb.option(
    "limit", "Number of messages to retrieve", int, required=False, default=-1
)
@lightbulb.option(
    "from_date", "Date to retrieve messages back to", required=False, type=datetime
)
@lightbulb.option("format", "JSON or TXT", choices=["JSON", "TXT"], default="TXT")
@lightbulb.command(
    "retrieve",
    "Retrieve previous messages",
    auto_defer=True,
)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def retrieve(ctx: lightbulb.Context):
    syslog.warning(
        f"Retrieving messages in {ctx.channel_id} requested by {ctx.author.username} ({ctx.author.id})"
    )
    chan: hikari.TextableChannel = ctx.get_channel()
    guild: hikari.Guild = ctx.get_guild()
    history = chan.fetch_history()

    fmt = ctx.options["format"]
    if fmt == "TXT":
        data = []
    elif fmt == "JSON":
        data = {}
    limit = ctx.options["limit"]
    async for message in history:
        if limit > 0:
            limit -= 1
        else:
            break

        mem = message.member
        if not mem:
            mem = guild.get_member(message.author.id)
        mess = nice_message(mess_obj=message, memb_obj=mem)

        if fmt == "TXT":
            data.append(mess.stringise())
        elif fmt == "JSON":
            data[mess.message_id] = mess.jsonise()

        time.sleep(0.005)

    file_path = Paths.data.joinpath(
        f"{guild.name}_{chan.name}_{get_time()}.{fmt.lower()}"
    )

    if fmt == "TXT":
        Read_Write.write_txt(data="\n".join(data), file=file_path)
    elif fmt == "JSON":
        Read_Write.write_json(data=data, file=file_path)
    await ctx.respond("Message archive", attachment=file_path)
