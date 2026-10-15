# TheGarden

A Discord bot that posts clickable Pokéballs while a Pokétwo incense is active.

## Setup

1. Create a Discord application and bot, then invite it to your server with permission to view and send messages and use buttons.
2. Enable the **Message Content Intent** for the bot in the Discord Developer Portal.
3. Copy `.env.example` to `.env` and set `DISCORD_TOKEN` to your bot token.
4. Install dependencies and run the bot:

	```bash
	python -m pip install -r requirements.txt
	python main.py
	```

The bot watches public messages from Pokétwo (bot ID `716390085896962058`) for text containing `incense` and one of the start markers. It then posts in that channel at random intervals of 2 to 4 minutes. It stops when it sees a stop marker or after `INCENSE_DURATION_MINUTES` (60 by default). If Pokétwo uses different wording, adjust `INCENSE_START_MARKERS` or `INCENSE_STOP_MARKERS` in `.env` to match its public message text.

When a player opens a Pokéball, the bot posts a random Pokémon image and announces `You found PokémonName @user`. The Pokéball image is optional; place the provided image at `assets/pokeball.png` or set `POKEBALL_IMAGE_PATH` to its location. Pokémon images are loaded from PokéAPI, so an OpenAI API key is not needed.