import discord
from discord.ext import commands
import os
import datetime as dt
import pandas as pd

if "src" not in os.listdir():
    os.chdir("../../")
try:
    intents = discord.Intents.default()
    intents.members = True
    client = commands.Bot(command_prefix = '.', case_insensitive=True,  intents=intents)
except:
    client = commands.Bot(command_prefix = '.', case_insensitive=True)

LIMIT=100
OLDEST_FIRST=False

BOT_TOKEN = 'NzU0MDAyMzEwNTM5MTE2NTQ0.X1uZXw.lfvGKH-SJw54LEC0m-xUPxjsyIM'
CREDS = BOT_TOKEN
UTOPIA = 679921845671035034

parent_dir = os.getcwd()
if not os.path.isdir("data/DISCORD"):
    os.mkdir("data/DISCORD")


@client.event
async def on_ready():
    print("Bot is Ready, Scraping discord")
    server_name = "UTOPIA"
    utopia = client.get_guild(UTOPIA)
    channels = utopia.channels
    for channel in channels:
        if type(channel) == discord.channel.TextChannel:
            try:
                messages = await channel.history(limit=LIMIT, oldest_first=OLDEST_FIRST).flatten()
                print(channel.id, channel.name, len(messages))
                if not os.path.isdir("data/DISCORD/"+server_name):
                    os.mkdir("data/DISCORD/"+server_name)
                data = []
                for message in messages:
                    data.append(
                        {"author": message.author, 
                        "content": message.content, 
                        "created_at": message.created_at,
                        "clean_content": message.clean_content,
                        "reactions": len(message.reactions)}
                        )
                channel_df = pd.DataFrame(data)
                channel_df.to_csv("data/DISCORD/"+server_name+"/"+channel.name+".csv")
            except:
                print("Failed on", channel.name)
    client.close()

client.run(CREDS)