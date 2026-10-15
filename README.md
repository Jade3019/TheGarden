# TheGarden

A Discord bot that posts clickable Pokéballs at random times.

## Setup

1. Create a Discord application and bot, then invite it to your server with permission to view and send messages and use buttons.
2. Enable the **Message Content Intent** for the bot in the Discord Developer Portal.
3. Copy `.env.example` to `.env` and set `DISCORD_TOKEN` to your bot token.
4. Install dependencies and run the bot:

	```bash
	python -m pip install -r requirements.txt
	python main.py
	```

A Pokéball spawns every 2 to 4 minutes (`SPAWN_MIN_SECONDS` / `SPAWN_MAX_SECONDS`) in a random text channel the bot can post in. Set `ALLOWED_CHANNEL_IDS` (comma-separated) to limit which channels are used.

The first player to click a Pokéball turns it into a random Pokémon (official artwork from PokéAPI, saved in `assets/pokemon/` with names in `pokemon_names.json`), and the bot replies `You found PokémonName! @user`. Place the Pokéball image at `assets/pokeball.png` or set `POKEBALL_IMAGE_PATH`; without it, a small PokéAPI sprite is used.

`v.test` posts a Pokéball in the current channel. It only works for members with the role listed in `RESERVE_MANAGER_ROLE` (comma-separated role names, role IDs or user IDs; default `1532820386511720579`) and, if `ALLOWED_CHANNEL_IDS` is set, only in those channels.
