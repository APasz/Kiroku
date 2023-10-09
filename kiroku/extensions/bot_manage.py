import logging
from lightbulb import errors

import lightbulb

from .. import SYSLOG
from ..store import Store

print(__name__)

syslog = logging.getLogger(SYSLOG)

plugin = lightbulb.Plugin(
    name="Bot Manage",
    description="Module housing commands for managing the bot",
)
plugin.add_checks(lightbulb.owner_only)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)


@plugin.command
@lightbulb.command("shutdown", "Shut the bot down", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def shutdown(ctx: lightbulb.Context):
    syslog.warning("Shutdown signal received")
    await ctx.respond("Shutting down...")
    await ctx.bot.close()


@plugin.command
@lightbulb.command("ensure", "Ensure commands", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def ensure(ctx: lightbulb.Context):
    syslog.info("Ensuring commands")
    await ctx.bot.sync_application_commands()
    await ctx.respond("Done!")


@plugin.command
@lightbulb.command("ext", "Extensions Group", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def ext(ctx: lightbulb.Context):
    await ext_list(ctx)


@ext.child
@lightbulb.command("list", "List loaded extensions", ephemeral=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def ext_list(ctx: lightbulb.Context):
    ext_str = ""
    for ext in Store.extensions_dict.keys():
        ext_str = f"{ext_str}\n{ext}"
    await ctx.respond(f"Currently loaded extensions;\n{ext_str}")


@ext.child
@lightbulb.option(
    "ext", "The extension to load", choices=list(Store.extensions_dict.keys())
)
@lightbulb.command("load", "Load an extension", ephemeral=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def ext_load(ctx: lightbulb.Context):
    ext = ctx.options.ext
    ext_str = f"**{ext}** extension "
    try:
        ctx.bot.load_extensions(Store.extensions_dict[ext])
        await ctx.respond(ext_str + "was loaded.")
    except errors.ExtensionNotFound:
        syslog.exception(f"{ext}")
        await ctx.respond(ext_str + "was not found!")

    except errors.ExtensionAlreadyLoaded:
        syslog.exception(f"{ext}")
        await ctx.respond(ext_str + "is already loaded!")

    except errors.ExtensionMissingLoad:
        syslog.exception(f"{ext}")
        await ctx.respond(ext_str + "is missing load function!")


@ext.child
@lightbulb.option(
    "ext", "The extension to unload", choices=list(Store.extensions_dict.keys())
)
@lightbulb.command("unload", "Unload an extension", ephemeral=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def ext_unload(ctx: lightbulb.Context):
    ext = ctx.options.ext
    ext_str = f"**{ext}** extension "
    try:
        ctx.bot.unload_extensions(Store.extensions_dict[ext])
        await ctx.respond(ext_str + "was unloaded.")
    except errors.ExtensionNotFound:
        syslog.exception(f"{ext}")
        await ctx.respond(ext_str + "was not found!")

    except errors.ExtensionNotLoaded:
        syslog.exception(f"{ext}")
        await ctx.respond(ext_str + "is not loaded!")

    except errors.ExtensionMissingUnload:
        syslog.exception(f"{ext}")
        await ctx.respond(ext_str + "is missing unload function!")


@ext.child
@lightbulb.option(
    "ext", "The extension to reload", choices=list(Store.extensions_dict.keys())
)
@lightbulb.command("reload", "Reload an extension", ephemeral=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def ext_reload(ctx: lightbulb.Context):
    await ext_unload(ctx)
    await ext_load(ctx)


# MIT APasz
