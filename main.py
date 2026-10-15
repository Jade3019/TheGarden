import os
import random
import time
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
POKETWO_BOT_ID = int(os.getenv("POKETWO_BOT_ID", "716390085896962058"))
INCENSE_DURATION_MINUTES = int(os.getenv("INCENSE_DURATION_MINUTES", "60"))
POKEBALL_IMAGE_PATH = Path(os.getenv("POKEBALL_IMAGE_PATH", "assets/pokeball.png"))
START_MARKERS = tuple(
    marker.strip().lower()
    for marker in os.getenv("INCENSE_START_MARKERS", "activated,started,used,is active").split(",")
    if marker.strip()
)
STOP_MARKERS = tuple(
    marker.strip().lower()
    for marker in os.getenv("INCENSE_STOP_MARKERS", "expired,ended,finished,has run out").split(",")
    if marker.strip()
)

if not DISCORD_TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your .env file before starting the bot.")

intents = discord.Intents.default()
intents.message_content = True


class CatchView(discord.ui.View):
    def __init__(self, bot: "GardenBot") -> None:
        super().__init__(timeout=600)
        self.bot = bot
        self.caught = False

    @discord.ui.button(
        label="Open Pokéball",
        emoji="🔴",
        style=discord.ButtonStyle.danger,
        custom_id="garden:open_pokeball",
    )
    async def open_pokeball(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.caught:
            await interaction.response.send_message(
                "This Pokéball has already been opened.", ephemeral=True
            )
            return

        self.caught = True
        button.disabled = True
        await interaction.response.edit_message(view=self)

        pokemon_id = random.randint(1, 1025)
        try:
            async with self.bot.http_session.get(
                f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
            ) as response:
                response.raise_for_status()
                pokemon = await response.json()
        except (aiohttp.ClientError, TimeoutError):
            await interaction.followup.send(
                "Could not load the Pokémon image. Please try again later.",
                ephemeral=True,
            )
            return

        name = pokemon["name"].replace("-", " ").title()
        image_url = pokemon["sprites"].get("front_default")
        embed = discord.Embed()
        if image_url:
            embed.set_image(url=image_url)

        if interaction.channel is not None:
            await interaction.channel.send(
                content=f"You found **{name}** <@{interaction.user.id}>",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(users=True),
            )


class GardenBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="v.", intents=intents)
        self.http_session: aiohttp.ClientSession | None = None
        self.incense_channel_id: int | None = None
        self.incense_expires_at = 0.0
        self.next_spawn_at = 0.0

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
        if not self.incense_channel_id:
            return
        if time.time() >= self.incense_expires_at:
            self.incense_channel_id = None
            return
        if time.monotonic() < self.next_spawn_at:
            return

        channel = self.get_channel(self.incense_channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(self.incense_channel_id)
            except discord.HTTPException:
                self.incense_channel_id = None
                return

        await self.spawn_pokeball(channel)
        self.next_spawn_at = time.monotonic() + random.randint(120, 240)

    async def spawn_pokeball(self, channel: discord.abc.Messageable) -> None:
        embed = discord.Embed(
            title="A Pokéball appeared!",
            description="Open the Pokéball to see which Pokémon is inside.",
        )
        if POKEBALL_IMAGE_PATH.is_file():
            image = discord.File(POKEBALL_IMAGE_PATH, filename="pokeball.png")
            embed.set_image(url="attachment://pokeball.png")
            await channel.send(embed=embed, file=image, view=CatchView(self))
        else:
            await channel.send(embed=embed, view=CatchView(self))

    @spawn_loop.before_loop
    async def before_spawn_loop(self) -> None:
        await self.wait_until_ready()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.id != POKETWO_BOT_ID:
            await self.process_commands(message)
            return

        parts = [message.content]
        for embed in message.embeds:
            parts.extend([embed.title or "", embed.description or ""])
            parts.extend(f"{field.name} {field.value}" for field in embed.fields)
        text = " ".join(parts).lower()
        if "incense" not in text:
            return

        if any(marker in text for marker in STOP_MARKERS):
            self.incense_channel_id = None
            return

        if any(marker in text for marker in START_MARKERS):
            self.incense_channel_id = message.channel.id
            self.incense_expires_at = time.time() + INCENSE_DURATION_MINUTES * 60
            self.next_spawn_at = time.monotonic() + random.randint(120, 240)


bot = GardenBot()


@bot.command(name="test")
async def test(ctx: commands.Context) -> None:
    await bot.spawn_pokeball(ctx.channel)


bot.run(DISCORD_TOKEN)