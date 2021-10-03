import discord
from discord.ext import commands
import os
import datetime as dt
from discord.utils import get, to_json
import pandas as pd
import json

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
GET_ALL_CHANNELS=False
DESIRED_CHANNELS=[795072400403857469,713081521925521469,816786354905022516,858885212364079104,713082942527897650,839612987370504253,876561218234646588,876561254985134170,877925838065131530,679928623540600883,837703231916343327,679928248121032716,806194061114998804]

BOT_TOKEN = 'NzU0MDAyMzEwNTM5MTE2NTQ0.X1uZXw.lfvGKH-SJw54LEC0m-xUPxjsyIM'
CREDS = BOT_TOKEN
UTOPIA = 679921845671035034

parent_dir = os.getcwd()
if not os.path.isdir("data/DISCORD"):
    os.mkdir("data/DISCORD")


primitive = (int, str, bool, dict)

def is_primitive(obj):
    return type(obj) in primitive

def has_string_method(obj):
    return type(obj).__str__ is not object.__str__

def get_json(obj):
    dict_data = []
    if not has_string_method(obj):
        for name in dir(obj):
            if not name.startswith('_') and name != "call":
                try:
                    value = getattr(obj, name)
                    if is_primitive(value):
                        dict_data.append((name, value))
                    elif type(value) is list:
                        dict_data.append((name, [get_json(obj) for obj in value]))
                    elif not callable(value):
                        dict_data.append((name, get_json(value)))
                except:
                    print("failed on", name)
    else:
        return str(obj)
    return dict(dict_data)

@client.event
async def on_ready():
    print("Bot is Ready, Scraping discord")
    server_name = "UTOPIA"
    utopia = client.get_guild(UTOPIA)
    channels = utopia.channels
    if not GET_ALL_CHANNELS:
        channels = [channel for channel in channels if channel.id in DESIRED_CHANNELS]
    data = {}
    for channel in channels:
        if type(channel) == discord.channel.TextChannel:
            try:
                messages = await channel.history(limit=LIMIT, oldest_first=OLDEST_FIRST).flatten()
                print(channel.id, channel.name, len(messages))
                messages_data = []
                for message in messages:
                    message_data = get_json(message)
                    messages_data.append(message_data)
                data[channel.name] = messages_data
            except:
                print("Failed on", channel.name)
    with open('data/DISCORD/'+server_name+'.json', 'w') as fp:
        json.dump(data, fp,  indent=4)
    client.close()

client.run(CREDS)