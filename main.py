import os

from dotenv import load_dotenv

from bot import FarmBot

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your .env file before starting the bot.")

FarmBot().run(DISCORD_TOKEN)
