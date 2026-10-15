import json
import os
import random
import time
from collections import deque
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POKETWO_BOT_ID = int(os.getenv("POKETWO_BOT_ID", "716390085896962058"))
POKEBALL_BURST_SPAWNS = int(os.getenv("POKEBALL_BURST_SPAWNS", "10"))
BURST_WINDOW_SECONDS = 60
BURST_IDLE_SECONDS = 120
POKEBALL_INTERVAL_SECONDS = 60
RESERVE_MANAGER_ROLE = os.getenv("RESERVE_MANAGER_ROLE", "Reserve Manager").strip()
ALLOWED_CHANNEL_IDS = {
    int(value) for value in os.getenv("ALLOWED_CHANNEL_IDS", "").split(",") if value.strip()
}
POKEBALL_IMAGE_PATH = Path(os.getenv("POKEBALL_IMAGE_PATH", "assets/pokeball.png"))
POKEBALL_FALLBACK_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png"
)
POKEMON_IDS = json.loads(Path(__file__).with_name("pokemon_ids.json").read_text())

if not DISCORD_TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your .env file before starting the bot.")

intents = discord.Intents.default()
intents.message_content = True


class CatchView(discord.ui.View):
    def __init__(self, bot: "GardenBot") -> None:
        super().__init__(timeout=600)
        self.bot = bot
        self.caught = False

    @discord.ui.button(emoji="🔴", style=discord.ButtonStyle.secondary)
    async def open_pokeball(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.caught:
            await interaction.response.send_message(
                "This Pokéball has already been opened.", ephemeral=True
            )
            return

        # Claim before any await so only the first click wins.
        self.caught = True
        await interaction.response.defer()

        try:
            name, image_url = await self.bot.random_pokemon()
        except (aiohttp.ClientError, TimeoutError, LookupError):
            self.caught = False
            await interaction.followup.send(
                "Could not load the Pokémon. Please try again.", ephemeral=True
            )
            return

        embed = discord.Embed(title=name)
        embed.set_image(url=image_url)

        self.stop()
        message = await interaction.edit_original_response(
            embed=embed, attachments=[], view=None
        )
        await message.reply(
            f"You found {name}! <@{interaction.user.id}>",
            allowed_mentions=discord.AllowedMentions(users=True),
        )


class GardenBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="v.", intents=intents)
        self.http_session: aiohttp.ClientSession | None = None
        self.recent_spawns: deque[tuple[float, int]] = deque()
        self.burst_active = False
        self.next_ball_at = 0.0

    async def random_pokemon(self) -> tuple[str, str]:
        # Some forms have no artwork, so retry with another entry.
        for _ in range(10):
            pokemon_id = random.choice(POKEMON_IDS)
            async with self.http_session.get(
                f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            ) as response:
                response.raise_for_status()
                pokemon = await response.json()
            sprites = pokemon["sprites"]
            image_url = (
                sprites["other"]["official-artwork"]["front_default"]
                or sprites["front_default"]
            )
            if image_url:
                return pokemon["name"].replace("-", " ").title(), image_url
        raise LookupError("No Pokémon with an image found")

    async def setup_hook(self) -> None:
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        )
        self.spawn_loop.start()

    async def close(self) -> None:
        self.spawn_loop.cancel()
        if self.http_session:
            await self.http_session.close()
        await super().close()

    @tasks.loop(seconds=5)
    async def spawn_loop(self) -> None:
        now = time.monotonic()
        self.prune_spawns(now)
        if not self.burst_active:
            return
        if not self.recent_spawns:
            self.burst_active = False
            return
        if now < self.next_ball_at:
            return

        channel_id = random.choice({channel for _, channel in self.recent_spawns})
        channel = self.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except discord.HTTPException:
                return

        self.next_ball_at = now + POKEBALL_INTERVAL_SECONDS
        await self.spawn_pokeball(channel)

    def prune_spawns(self, now: float) -> None:
        while self.recent_spawns and now - self.recent_spawns[0][0] > BURST_IDLE_SECONDS:
            self.recent_spawns.popleft()

    async def spawn_pokeball(self, channel: discord.abc.Messageable) -> None:
        embed = discord.Embed()
        if POKEBALL_IMAGE_PATH.is_file():
            image = discord.File(POKEBALL_IMAGE_PATH, filename="pokeball.png")
            embed.set_image(url="attachment://pokeball.png")
            await channel.send(embed=embed, file=image, view=CatchView(self))
        else:
            embed.set_image(url=POKEBALL_FALLBACK_URL)
            await channel.send(embed=embed, view=CatchView(self))

    @spawn_loop.before_loop
    async def before_spawn_loop(self) -> None:
        await self.wait_until_ready()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.id != POKETWO_BOT_ID:
            await self.process_commands(message)
            return

        titles = [embed.title or "" for embed in message.embeds]
        text = " ".join([message.content, *titles]).lower()
        if "wild pokémon has appeared" not in text:
            return
        if ALLOWED_CHANNEL_IDS and message.channel.id not in ALLOWED_CHANNEL_IDS:
            return

        now = time.monotonic()
        self.recent_spawns.append((now, message.channel.id))
        self.prune_spawns(now)
        in_window = sum(
            1 for stamp, _ in self.recent_spawns if now - stamp <= BURST_WINDOW_SECONDS
        )
        if not self.burst_active and in_window >= POKEBALL_BURST_SPAWNS:
            self.burst_active = True
            self.next_ball_at = now


bot = GardenBot()


def can_use_test(ctx: commands.Context) -> bool:
    if ALLOWED_CHANNEL_IDS and ctx.channel.id not in ALLOWED_CHANNEL_IDS:
        return False
    if not isinstance(ctx.author, discord.Member):
        return False
    wanted = RESERVE_MANAGER_ROLE.lower()
    return any(
        str(role.id) == wanted or role.name.lower() == wanted for role in ctx.author.roles
    )


@bot.command(name="test")
@commands.check(can_use_test)
async def test(ctx: commands.Context) -> None:
    await bot.spawn_pokeball(ctx.channel)


@test.error
async def test_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if not isinstance(error, commands.CheckFailure):
        raise error


bot.run(DISCORD_TOKEN)