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
token_regex = re.compile(r'\S+')
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

        # if no arguments are passed, default to 'help.txt'
        if len(tokens) == 0:
            tokens = ['help.txt']

        replied_tokens = []
        responses = []
        for t in tokens:
            # replace double quotes in t with the string quote,
            # since that's what appears in the help docs
            t = t.replace('"', 'quote')

            # check if we've responded to this query already
            if t in replied_tokens:
                print('already replied to {}, skipping'.format(t))
                continue

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

                # perform case insensitive search
                entry = (t,)
                query = 'SELECT * FROM tags WHERE UPPER(tag)=UPPER(?)'
                result = cursor.execute(query, entry).fetchone()

            if result is None:
                print('case-insensitive search for {} could not be found'.format(t))
                print('tag {} is not in tags.db'.format(t))
            else:
                tag = result[0]
                doc = result[1]
                link = build_link(doc, tag)
                replied_tokens.insert(0, t)

                # check that url gets a response
                request = requests.head(link)
                if request.ok:
                    responses.insert(len(responses), '`:h {}`: {}'.format(tag, link))

        if len(responses) > 0:
            if len(responses) == 1:
                msg = 'Help page for {}'.format(responses[0])
            else:
                msg = 'Help pages for:\n'
                for r in responses:
                    msg += '• ' + r + '\n'
            await message.channel.send(msg)

client.run(discord_token)
