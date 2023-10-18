from datetime import datetime
from pathlib import Path as Pathy
import pytz
import logging
import hikari

from .. import SYSLOG, DATE_FORMAT, MESS_SIZE
from ..store import Store
from ..util.file import bytes_to_human, Paths

print(__name__)

syslog = logging.getLogger(SYSLOG)

MELB_TZ = pytz.timezone("Australia/Melbourne")


def find_link_expiry(link: str) -> int:
    times = link.rsplit("ex=")[-1]
    ex = times.split("&")[0]
    exp = int(float.fromhex(ex))
    return exp


def timestamp_to_local(ts: int | float) -> str:
    time = datetime.fromtimestamp(float(ts), tz=MELB_TZ)
    return time.strftime(DATE_FORMAT)


class nice_message:
    """Transform message into something more convenient"""

    def __init__(
        self,
        mess_obj: hikari.Message,
        memb_obj: hikari.Member | None,
        guil_obj: hikari.Guild,
        chan_obj: hikari.TextableChannel,
    ) -> None:
        syslog.debug("Making message nice")

        self.guild = guil_obj
        self.guild_id = guil_obj.id

        self.channel_name = chan_obj.name
        self.channel_id = chan_obj.id

        if isinstance(memb_obj, hikari.Member):
            self.member: hikari.Member = memb_obj
            self.member_id = int(memb_obj.id)
            self.member_nick = self.member.nickname
            self.member_display = self.member.display_name
        if not memb_obj:
            syslog.info("Member unretrievable")
            self.member: hikari.User = mess_obj.author
            self.member_id = int(mess_obj.author.id)
            self.member_nick = None
            self.member_display = self.member.username

        self.message = mess_obj
        self.message_id = int(mess_obj.id)
        self.message_content = mess_obj.content

        self.created_at = round(mess_obj.created_at.timestamp(), 3)
        self.created_at_local = timestamp_to_local(self.created_at)

        self.edited_at = mess_obj.edited_timestamp
        if self.edited_at is not None:
            self.edited_at = round(self.edited_at.timestamp(), 3)
            self.edited_at_local = timestamp_to_local(self.edited_at)

        if mess_obj.attachments:
            self.attachments = mess_obj.attachments
            self.attachment_count = len(mess_obj.attachments)
        else:
            self.attachment_count = 0
        if mess_obj.embeds:
            self.embeds = mess_obj.embeds
            self.embed_count = len(mess_obj.embeds)
        else:
            self.embed_count = 0

    def jsonise(self) -> dict:
        """Transform into nice JSON format"""
        syslog.debug("JSONising message")

        def attach_dict(attach: hikari.Attachment) -> dict:
            exp = find_link_expiry(attach.url)
            data = {
                "id": attach.id,
                "media_type": attach.media_type,
                "size": attach.size,
                "size_nice": bytes_to_human(attach.size),
                "filename": attach.filename,
                "url": attach.url,
                "url_expiry": exp,
                "url_expiry_local": timestamp_to_local(exp),
            }
            return data

        def embed_dict(embed: hikari.Embed) -> dict:
            data = {}
            if embed.title:
                data["title"] = embed.title
            if embed.url:
                data["url"] = embed.url
            if embed.author:
                data["author"] = embed.author.name
                if embed.author.url:
                    data["author_url"] = embed.author.url
            if embed.provider:
                data["provider"] = embed.provider.name
            return data

        data = {
            "author": {
                "id": self.member_id,
                "user": self.member.username,
                "global": self.member.global_name,
                "nick": self.member_nick,
                "is_bot": self.member.is_bot,
                "is_system": self.member.is_system,
            },
            "content": self.message_content,
            "message_id": self.message_id,
            "message_link": self.message.make_link(guild=self.guild),
            "created_at_ts": self.created_at,
            "created_at_local": self.created_at_local,
        }

        if self.edited_at:
            data["edited_at_ts"] = self.edited_at
            data["edited_at_local"] = self.edited_at_local

        if self.attachment_count > 0:
            data["attachment_count"] = self.attachment_count
            data["attachments"] = []
            for attach in self.attachments:
                data["attachments"].append(attach_dict(attach=attach))

        if self.embed_count > 0:
            data["embed_count"] = self.embed_count
            data["embeds"] = []
            for embed in self.embeds:
                data["embeds"].append(embed_dict(embed=embed))

        return data

    def stringise(self):
        """Return in nice string format"""
        syslog.debug("STRINGising message")

        def attach_str(attach: hikari.Attachment) -> str:
            exp = find_link_expiry(attach.url)
            text = [
                f"\tID: {attach.id} | Type: {attach.media_type}",
                f"\tSize: {bytes_to_human(attach.size)} | {attach.size}Bytes",
                f"\tFilename: {attach.filename}",
                f"\tURL: {attach.url}",
                f"\tURL Expiry: {timestamp_to_local(exp)} | {exp}",
            ]
            return "\n".join(text)

        def embed_str(embed: hikari.Embed) -> str:
            text = []
            if embed.title:
                text.append(f"\tTitle: {embed.title}")
            if embed.url:
                text.append(f"\tURL: {embed.url}")
            if embed.author:
                text.append(f"\tAuthor: {embed.author.name}")
                if embed.author.url:
                    text.append(f"\tAuthor URL: {embed.author.url}")
            if embed.provider:
                text.append(f"\tProvider: {embed.provider.name}")
            return "\n".join(text)

        text = []

        userline = "User: {u} | Global: {g} | Nick: {n} | ID: {i}".format(
            u=self.member.username,
            g=self.member.global_name,
            n=self.member_nick,
            i=self.member_id,
        )

        if self.member.is_bot:
            userline += " | IS_BOT"
        if self.member.is_system:
            userline += " | IS_SYSTEM"
        text.append(userline)

        text.append(f"Content: {self.message_content}")

        text.append(
            f"Message ID: {self.message_id}" + (" (Edited)" if self.edited_at else "")
        )

        text.append(
            f"Message Link: {self.message.make_link(guild=self.guild)}",
        )

        creationline = f"Created at: {self.created_at_local} | {self.created_at}"
        text.append(creationline)

        if self.edited_at:
            editedline = f"Edited at: {self.edited_at_local} | {self.edited_at}"
            text.append(editedline)

        if self.attachment_count > 0:
            for attach in self.attachments:
                text.append(f"Attachments  {self.attachment_count}")
                text.append(attach_str(attach))

        if self.embed_count > 0:
            for embed in self.embeds:
                text.append(f"Embeds  {self.embed_count}")
                text.append(embed_str(embed))

        text.append("\n")
        return "\n".join(text)

    def stringise_compact(self):
        """Return in nice compact string format"""
        syslog.debug("STRINGising message compactly")

        embed = attach = " "
        if self.attachment_count > 0:
            attach = "A"
        if self.embed_count > 0:
            embed = "E"

        return f"{self.member_display:36}|{self.created_at_local}|{attach}{embed}| {self.message_content}"


def create_logger(file_path: Pathy) -> logging.Logger:
    """Creates a logging object"""
    syslog.info("Creating logger")

    file_path.parent.mkdir(exist_ok=True, parents=True)

    log = logging.getLogger(file_path.stem)
    log.setLevel("INFO")

    handle_file = logging.handlers.RotatingFileHandler(
        filename=file_path,
        maxBytes=MESS_SIZE,
        encoding="utf-8",
    )
    handle_file.setFormatter(
        logging.Formatter(
            "%(asctime)s|%(created).0f || %(message)s",
            DATE_FORMAT,
        )
    )
    log.addHandler(handle_file)

    return log


def get_logger(mess: nice_message, chan_name: str, guild_name: str) -> logging.Logger:
    """Return the logger object associated with a channel"""

    guild = f"{guild_name}_({mess.guild_id})"
    channel = f"{chan_name}_({mess.channel_id})"

    if guild not in Store.logs:
        Store.logs[guild] = {}
    if channel not in Store.logs[guild]:
        log_file = Paths.logs.joinpath(guild, f"{channel}.log")
        Store.logs[guild][channel] = create_logger(log_file)
    return Store.logs[guild][channel]
