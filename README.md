# TheGarden

A Discord bot that posts clickable Pokéballs when Pokétwo spawns come in fast.

## Setup

1. Create a Discord application and bot, then invite it to your server with permission to view and send messages and use buttons.
2. Enable the **Message Content Intent** for the bot in the Discord Developer Portal.
3. Copy `.env.example` to `.env` and set `DISCORD_TOKEN` to your bot token.
4. Install dependencies and run the bot:

	```bash
	python -m pip install -r requirements.txt
	python main.py
	```

The bot watches public Pokétwo spawn messages (bot ID `716390085896962058`). Once `POKEBALL_BURST_SPAWNS` (10 by default) spawns are seen within a minute, it posts a Pokéball every minute in a random channel that recently had spawns. It stops about 2 minutes after the spawns stop.

The first player to click a Pokéball turns it into a random Pokémon (official artwork from PokéAPI, IDs listed in `pokemon_ids.json`), and the bot replies `You found PokémonName! @user`. Place the Pokéball image at `assets/pokeball.png` or set `POKEBALL_IMAGE_PATH`; without it, a small PokéAPI sprite is used.

`v.test` posts a Pokéball in the current channel. It only works for members with the role named in `RESERVE_MANAGER_ROLE` (name or ID) and, if `ALLOWED_CHANNEL_IDS` is set, only in those channels.
