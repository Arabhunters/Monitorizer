import discord
import asyncio
import os 


class DiscordReport:
    def start_reporter_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_reporter())
        loop.close()
        
    async def start_reporter(self):
        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)
        await self.client.start(self.discord_reporter_token)

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
    
        send_fut = asyncio.run_coroutine_threadsafe(send_message(), self.client.loop)
        # Wait for the coroutine to finish
        send_fut.result()