import asyncio
import discord
import os
from discord.ext import commands
from monitorizer.core.config import Config
from monitorizer.ui.arguments import args
# Local imports
from monitorizer.globals import local_metadata, metadata_github
from monitorizer.core import flags
from modules.report.utils import reload_watchlist, rewrite_watchlist, is_alive
from modules.report import templates

config = Config()
watchlist = reload_watchlist()

class MonitorizerBot(discord.Bot):
    def __init__(self, intents, *args, **kwargs):
        super().__init__(intents=intents, *args, **kwargs)
    # async def start_reporter(self):
    #     intents = discord.Intents.all()
    #     self.client = discord.Client(intents=intents)
    def send_discord_report(self, msg):
        async def send_message():
            try:
                channel = self.client.get_channel(self.discord_reporter_channel)
                if not channel:
                    self.info("Channel not found")
                    raise RuntimeError(f"Could not find Discord channel with ID: {self.discord_reporter_channel}")
            except Exception as e:
                # Replace with your logging method
                self.info(str(e))
                return

            for _ in range(10):
                try:
                    with open('report.txt', 'w') as f:
                        f.write(msg)
                    await channel.send(file=discord.File('./report.txt'))
                    os.remove('report.txt')
                    # send the message as a file 
                    return
                except discord.HTTPException as e:
                    # Replace with your logging method
                    self.info(str(e))
                    await asyncio.sleep(30)
            
            # Assuming this is a method for local logging
            self.local(msg, reporter="discord")
            # loop = asyncio.new_event_loop() 
            send_fut = asyncio.run_coroutine_threadsafe(send_message(),self.client.loop)
            # Wait for the coroutine to finish
            send_fut.result()
            self.info(f"Discord Report Sent")


# Bot initialization
bot = MonitorizerBot(command_prefix="/", intents=discord.Intents.default(), discord_channel=config.discord_channel)
commands_group = bot.create_group(name='monitor')
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@commands_group.command(description='Sample command under "commands" group')
async def ping(ctx): 
    await ctx.respond("pong")

@commands_group.command(description='Help Command')
async def bothelp(ctx):
    code_base_update = True if float(local_metadata.get("version", {}).get("monitorizer", 0)) < float(
        metadata_github.get("version", {}).get("monitorizer", 0)) else False
    toolkit_update = True if float(local_metadata.get("version", {}).get("toolkit", 0)) < float(
        metadata_github.get("version", {}).get("toolkit", 0)) else False

    if code_base_update == True and toolkit_update == False:
        await ctx.respond(templates.help_msg.replace("{warning1}\n", "").format(
            warning0=templates.update_msg_codebase.format(
                metadata_github['changelog']['monitorizer']
            )
        ))

    if toolkit_update == True and code_base_update == False:
        await ctx.respond(templates.help_msg.replace("{warning1}\n", "").format(
            warning0=templates.update_msg_toolkit.format(
                metadata_github['changelog']['toolkit']
            )
        ))

    if toolkit_update == True and code_base_update == True:
        await ctx.respond(templates.help_msg.format(
            warning0=templates.update_msg_codebase.format(
                metadata_github['changelog']['monitorizer']
            ),
            warning1=templates.update_msg_toolkit.format(
                metadata_github['changelog']['toolkit']
            )
        ))

    await ctx.respond(templates.help_msg.replace("{warning0}\n", "").replace("{warning1}\n", ""))

@commands_group.command(description='Add New Targets Command')
async def add(ctx, targets):
    alive_targets = []

    targets = targets.split(',') if ',' in targets else [targets]
    
    for target in targets:
        if not is_alive(target) or target in watchlist:
            continue

        watchlist.append(target)
        alive_targets.append(target)

    rewrite_watchlist(watchlist)
    await ctx.respond("Added {} target(s) to watching list".format(len(alive_targets)))

@commands_group.command(description='Remove Targets Command')
async def remove(ctx, targets):
    targets = targets.split(',') if ',' in targets else [targets]

    for target in targets:
        if not target in watchlist:
            continue
        watchlist.remove(target)

    rewrite_watchlist(watchlist)
    await ctx.respond("Removed {} target(s) from watching list".format(len(targets)))

@commands_group.command(description='List Targets Command')
async def ls(ctx): 
    msg = ""
    targets = reload_watchlist()
    if len(targets) == 0:
        await ctx.respond("Watchlist is empty")
    for target in targets:
        msg += templates.target.format(target) + "\n"
    await ctx.respond(msg[:-1])


@commands_group.command(description='Change Scanning frequency')
async def freq(ctx, new_frequency):
    if len(new_frequency) == 0:
        await ctx.respond("Scanning frequency is one scan every {} hour(s)".format(flags.sleep_time))

    if str(new_frequency[0]).isdigit():
        flags.sleep_time = int(new_frequency[0])
        await ctx.respond("Scanning frequency updated to one scan every {} hour(s)".format(new_frequency[0]))
    else:
        await ctx.respond("Invalid number")

@commands_group.command(description='Change Concurrent working')
async def concurrent(ctx, new_concurrent):
    if len(new_concurrent) == 0:
        await ctx.respond("Concurrent working tools is {}/process".format(flags.concurrent))

    if str(new_concurrent[0]).isdigit():
        flags.concurrent = int(new_concurrent[0])
        await ctx.respond("Updated concurrent working tools to {}/process".format(new_concurrent[0]))
    else:
        await ctx.respond("Invalid number")

@commands_group.command(description='Show the status of the tool')
async def status(ctx):
    if flags.status == 'running':
        await ctx.respond(templates.run_status_msg.format(
            status=flags.status,
            target=flags.current_target,
            tool=flags.running_tool,
            report_name=flags.report_name,
        ))
    else:
        await ctx.respond(templates.stop_status_msg)

@commands_group.command(description='Send to Acuntix enable or disable')
async def acunetix(ctx, new_status):
    if len(new_status) == 0:
        await ctx.respond("Acunetix integration is " + ("enabled" if flags.acunetix else "disabled"))

    if new_status[0] == 'enable':
        flags.acunetix = True
        await ctx.respond("Acunetix integration is enabled. new targets will be sent automatically")

    if new_status[0] == 'disable':
        flags.acunetix = False
        await ctx.respond("Acunetix integration is disabled. no targets will be sent")