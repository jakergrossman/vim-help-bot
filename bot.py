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

# finds the most relevant help tag according
# to the following:
#
# If there is no full match for the pattern,
# or there are several matches, the "best"
# match will be used.
#
# - A match with the same case is much better
#   than a match with a different case
# - A match that starts after a non-alphanumeric
#   character is better than a match in the
#   middle of a word
# - A match at or near the beginning of the tag
#   is better than a match further on
# - The more alphanumeric characters match, the better.
# - The shorter the length of the match, the better.
def match_weight(match, tag):
    # weights
    case_weight      = 10000 # weight for correct case
    prev_char_weight = 1000  # weight for matches starting after [^a-zA-Z0-9]
    index_weight     = -100  # weight for index of match in tag
    alnum_weight     = 10    # weight for each matching [a-zA-Z0-9]
    length_weight    = -1    # weight for length of match

    # calculated tag weight
    weight = 0

    # get index of match
    idx = tag.find(match)

    weight += idx * index_weight

    # check case
    if match == tag[idx:idx+len(match)]:
        # exact case match
        weight += case_weight

    # check if previous char is alphanumeric, if applicable
    # NOTE: if match starts at beginning of tag, the weight
    # is still applied
    if len(tag) > 0:
        if idx > 0:
            if tag[idx-1].isalnum():
                weight += prev_char_weight
        else:
            weight += prev_char_weight

    # count number of alphanumeric matches
    for c in match:
        if c.isalnum():
            weight += alnum_weight

    # apply length weight
    weight += len(match) * length_weight

    # return tag weight
    return weight

def sort_matches(matches):
    sorted_matches = sorted(matches, key=lambda m: match_weight(m[0], m[1]))
    return sorted_matches

def fmt_help_tag(tag):
    search_query = tag

    # * -> star
    search_query = search_query.replace('*', 'star')

    # " -> quote
    search_query = search_query.replace('"', 'quote')

    return search_query

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
            # escape special characters
            t = fmt_help_tag(t)

            # check if we've responded to this query already
            if t in replied_tokens:
                print('already replied to {}, skipping'.format(t))
                continue

            query = 'SELECT * FROM tags WHERE tag=?'

            # check for exact match
            entry = (t,)
            exact_match = cursor.execute(query, entry).fetchone()

            if exact_match is not None:
                # exact match exists
                best_match = exact_match
            else:
                # no exact match, perform fuzzy match
                query = 'SELECT * FROM tags WHERE tag LIKE ? '

                # get result
                entry = ('%' + t + '%',)
                all_matches = cursor.execute(query, entry).fetchall()


                if len(all_matches) > 0:
                    best_match = sort_matches(all_matches)[0]
                else:
                    # no match for current token
                    continue

            if best_match is not None:
                tag = best_match[0]
                doc = best_match[1]
                link = build_link(doc, tag)
                replied_tokens.append(t)

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
