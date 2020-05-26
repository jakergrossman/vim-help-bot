# vim-help-bot
Discord bot that links to the relevant [vimhelp](https://vimhelp.org/) page

## Setup
First, clone the repository:
```
   git clone https://www.github.com/jakergrossman/vim-help-bot
   cd vim-help-bot
```

Next, lets install some dependencies
```
   pip3 install discord
   pip3 install python-dotenv
```

Now it's time to set up the discord bot token. Create a file `.env` and enter
your Discord API token in the following format:
```
   DISCORD_TOKEN=your_discord_token_here
```

## Usage
type `:h` followed by your query, e.g.:
```
   :h exrc
   :h statusline
   :h arabic
```
