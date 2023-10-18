import logging

from lightbulb import (
    CommandErrorEvent,
    NotOwner,
    CommandInvocationError,
    CommandIsOnCooldown,
    NotEnoughArguments,
    MissingRequiredPermission,
    BotMissingRequiredPermission,
    CheckFailure,
)

import lightbulb

from .. import SYSLOG


print(__name__)
syslog = logging.getLogger(SYSLOG)

plugin = lightbulb.Plugin(
    name="Error_Event", description="Module housing error event functions"
)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)


@plugin.listener(CommandErrorEvent)
async def on_error(event: CommandErrorEvent):
    exception = event.exception.__cause__ or event.exception
    respond = event.context.respond

    if isinstance(exception, CommandInvocationError):
        syslog.error(f"Invocation Error in {event.context.command.name}")
        raise exception

    elif isinstance(exception, NotOwner):
        syslog.warning(
            f"Non-Owner Invocation Attempt; {event.context.member.display_name} ({event.context.member.id})",
        )
        await respond("Only bot owner run this command.")

    elif isinstance(exception, CommandIsOnCooldown):
        await respond(
            f"Command cooldown `{exception.retry_after:.3f}`s.",
            delete_after=exception.retry_after,
        )

    elif isinstance(exception, NotEnoughArguments):
        miss_opts = event.exception.missing_options
        if miss_opts:
            miss = ", ".join(o.name.replace("_", " ") for o in miss_opts)
            await respond(f"Missing parameters: {miss}.")
        else:
            await respond("Too Many Parameters Passed.")

    elif isinstance(exception, MissingRequiredPermission):
        syslog.warning("User Missing Perms")
        await respond("You do not have permission.")

    elif isinstance(exception, BotMissingRequiredPermission):
        syslog.warning("Bot Missing Perms")
        perms = ", ".join(p.name.replace("_", " ") for p in exception.missing_perms)
        await respond(f"Can not perform action due to missing permission: {perms}.")

    elif isinstance(exception, CheckFailure):
        syslog.warning("A Check Failed")
        return None

    else:
        raise exception


# MIT APasz
