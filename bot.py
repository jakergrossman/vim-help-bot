import discord
import sqlite3
import requests
import re
from urllib.parse import quote
import os
from dotenv import load_dotenv

# Client setup
client = discord.Client()

# load .env
load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

# database connection
db = sqlite3.connect('tags.db')

# database cursor
cursor = db.cursor()

# regex to use to isolate tokens
token_regex = re.compile(r'[^\s]+')
command_regex = re.compile(r':(h|he|hel|help)')

@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user))

def build_link(doc, tag):
    return 'https://vimhelp.org/{}.txt.html#{}'.format(quote(doc), quote(tag))

@client.event
async def on_message(message):
    # if the message is from bot
    if message.author == client.user:
        return

    if command_regex.match(message.content) != None:
        # ignore first token, it is the command itself 
        tokens = token_regex.findall(message.content)[1:]
        for t in tokens:
            # get result
            entry = (t,)
            query = 'SELECT * FROM tags WHERE tag=?'
            result = cursor.execute(query, entry).fetchone()

            if result is None:
                print('base tag {} could not be found'.format(t))

                # wrap t in quotes and try again
                entry = ('\'' + t + '\'',)
                result = cursor.execute(query, entry).fetchone()

            if result is None:
                print('quoted tag \'{}\' could not be found'.format(t))

                # append ':' to beginning of t and try again
                entry = (':' + t,)
                result = cursor.execute(query, entry).fetchone()

            if result is None:
                print('colon-prefixed tag :{} could not be found'.format(t))
            else:
                tag = result[0]
                doc = result[1]
                link = build_link(doc, tag)

                # check that url gets a response
                request = requests.head(link)
                if request.ok:
                    reply = 'Help for `:h {}`: {}'.format(t, link)
                    await message.channel.send(reply)

client.run(discord_token)
