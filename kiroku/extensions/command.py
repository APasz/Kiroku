import logging
import string
import time
import hikari

import lightbulb
from datetime import datetime
from pathlib import Path as Pathy
from dateutil import parser
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


def parse_time(time: str) -> datetime | bool:
    """"""
    time = time.strip()

    def floaty(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    try:
        if not time[:4].isnumeric():  # dmy
            return parser.parse(timestr=time, dayfirst=True)
        elif time[4] in string.punctuation:  # iso
            return parser.parse(timestr=time, yearfirst=True)
        elif floaty(time):  # ts
            return datetime.fromtimestamp(float(time))
    except Exception:
        syslog.exception("Parser error")
        return False
    return False


@plugin.command
@lightbulb.command("get", "Get real time message log files for current Guild")
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

    await ctx.respond("Message Logs", attachment=zipfile)


@plugin.command
@lightbulb.option(
    name="limit",
    description="Number of messages to retrieve",
    type=int,
    required=False,
    default=-1,
)
@lightbulb.option(
    name="from_date",
    description="Date to retrieve messages back to. Timestamp | DMY | YMD",
    required=False,
    default=None,
)
@lightbulb.option(
    name="format",
    description="JSON | TXT (default) | TXT [COMPACT]",
    choices=["JSON", "TXT", "TXT [COMPACT]"],
    default="TXT",
)
@lightbulb.command(
    name="retrieve",
    description="Retrieve messages from current channel",
    auto_defer=True,
)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def retrieve(ctx: lightbulb.Context):
    chan: hikari.TextableChannel = ctx.get_channel()

    syslog.warning(
        f"Retrieving messages in {chan.name} ({chan.id}) requested by {ctx.author.username} ({ctx.author.id})"
    )

    guild: hikari.Guild = ctx.get_guild()

    perms = ctx.interaction.app_permissions
    if hikari.Permissions.ADMINISTRATOR not in perms:
        if hikari.Permissions.READ_MESSAGE_HISTORY not in perms:
            raise lightbulb.BotMissingRequiredPermission(
                perms=[hikari.Permissions.READ_MESSAGE_HISTORY]
            )

    from_ts = from_date = ctx.options["from_date"]
    if from_date:
        from_date = parse_time(from_date)
        if from_date:
            from_ts = int(from_date.timestamp())
        else:
            syslog.info("Unrecognisable from_date passed")
            await ctx.respond("From_date not recognised")
            return

    limit_tot = limit = ctx.options["limit"]
    if limit == -1:
        limit_tot = None

    syslog.warning(f"Message retrieval {limit=} {from_date=}")

    fmt = ctx.options["format"]
    JSON = TXT = COMPACT = False

    if "TXT" in fmt:
        TXT = True
        data = []
        if "COMPACT" in fmt:
            COMPACT = True
    elif "JSON" in fmt:
        JSON = True
        data = {}

    history = chan.fetch_history()

    total_messages = 0

    async for message in history:
        total_messages += 1

        if limit_tot:
            if limit > 0:
                limit -= 1
            else:
                syslog.info("reached message limit")
                break

        if from_date:
            if from_ts > message.created_at.timestamp():
                syslog.info("reached from_date limit")
                break

        mem = message.member
        if not mem:
            mem = guild.get_member(message.author.id)
        if not mem:
            try:
                mem = await ctx.app.rest.fetch_member(
                    guild=guild, user=message.author.id
                )
            except hikari.NotFoundError:
                syslog.error("Unknown Memeber: %s", message.author.id)
                mem = None
            except Exception:
                syslog.exception("Fetch Member")
                mem = None
        try:
            mess = nice_message(
                mess_obj=message, memb_obj=mem, chan_obj=chan, guil_obj=guild
            )
        except Exception:
            syslog.exception("Retrieval error")

        if TXT:
            if COMPACT:
                data.append(mess.stringise_compact())
            else:
                data.append(mess.stringise())
        elif JSON:
            data[str(mess.message_id)] = mess.jsonise()

        time.sleep(0.008)

    if TXT and COMPACT:
        fmt = "TXT"
    file_path = Paths.data.joinpath(
        f"{guild.name}_{chan.name}_{get_time()}.{fmt.lower()}"
    )

    if TXT:
        data.insert(
            0,
            f"Guild ID: {guild.id} | Channel ID: {chan.id} | Total Messages: {total_messages}",
        )

        sec_line = []
        if limit_tot:
            sec_line.append(f"Limit: {limit_tot}")
        if from_date:
            sec_line.append(f"From Date: {from_date} : {from_ts}")

        sec_line = " | ".join(sec_line)
        if len(sec_line) > 0:
            sec_line = sec_line + "\n"
            data.insert(1, sec_line)

        Read_Write.write_txt(data="\n".join(data), file=file_path)
    elif JSON:
        kata = {}
        kata["guild_id"] = guild.id
        kata["channel_id"] = chan.id
        kata["total_messages"] = total_messages
        if limit_tot:
            kata["limit"] = limit_tot
        if from_date:
            kata["from_date"] = f"{from_date} : {from_ts}"
        Read_Write.write_json(data=kata | data, file=file_path)
    await ctx.respond("Message archive", attachment=file_path)
