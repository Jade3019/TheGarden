import json
import os
import random
import time
from pathlib import Path

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SPAWN_MIN_SECONDS = int(os.getenv("SPAWN_MIN_SECONDS", "120"))
SPAWN_MAX_SECONDS = int(os.getenv("SPAWN_MAX_SECONDS", "240"))
RESERVE_MANAGER_ROLE = os.getenv("RESERVE_MANAGER_ROLE", "1532820386511720579").strip()
ALLOWED_CHANNEL_IDS = {
    int(value) for value in os.getenv("ALLOWED_CHANNEL_IDS", "").split(",") if value.strip()
}
ALLOWED_CATEGORY_IDS = {
    int(value)
    for value in os.getenv(
        "ALLOWED_CATEGORY_IDS",
        "1532135218792628315,1532137800974074077,1545882720935354418,1546208384385028146",
    ).split(",")
    if value.strip()
}


def is_allowed_channel(channel: discord.abc.GuildChannel) -> bool:
    if not ALLOWED_CHANNEL_IDS and not ALLOWED_CATEGORY_IDS:
        return True
    return channel.id in ALLOWED_CHANNEL_IDS or channel.category_id in ALLOWED_CATEGORY_IDS
POKEBALL_IMAGE_PATH = Path(os.getenv("POKEBALL_IMAGE_PATH", "assets/pokeball.png"))
POKEBALL_FALLBACK_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png"
)
BASE_DIR = Path(__file__).parent
POKEMON_NAMES: dict[str, str] = json.loads((BASE_DIR / "pokemon_names.json").read_text())


def random_pokemon() -> tuple[str, Path]:
    pokemon_id = random.choice(list(POKEMON_NAMES))
    name = POKEMON_NAMES[pokemon_id].replace("-", " ").title()
    return name, BASE_DIR / "assets" / "pokemon" / f"{pokemon_id}.png"

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

        name, image_path = random_pokemon()
        embed = discord.Embed(title=name)
        embed.set_image(url="attachment://pokemon.png")

        self.stop()
        message = await interaction.edit_original_response(
            embed=embed,
            attachments=[discord.File(image_path, filename="pokemon.png")],
            view=None,
        )
        await message.reply(
            f"You found {name}! <@{interaction.user.id}>",
            allowed_mentions=discord.AllowedMentions(users=True),
        )


class GardenBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="v.", intents=intents)
        self.next_ball_at = 0.0

    async def setup_hook(self) -> None:
        self.spawn_loop.start()

    async def close(self) -> None:
        self.spawn_loop.cancel()
        await super().close()

    def spawn_channels(self) -> list[discord.TextChannel]:
        channels = []
        for guild in self.guilds:
            for channel in guild.text_channels:
                if not is_allowed_channel(channel):
                    continue
                permissions = channel.permissions_for(guild.me)
                if permissions.send_messages and permissions.embed_links:
                    channels.append(channel)
        return channels

    @tasks.loop(seconds=5)
    async def spawn_loop(self) -> None:
        now = time.monotonic()
        if now < self.next_ball_at:
            return
        self.next_ball_at = now + random.randint(SPAWN_MIN_SECONDS, SPAWN_MAX_SECONDS)

        channels = self.spawn_channels()
        if channels:
            await self.spawn_pokeball(random.choice(channels))

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


bot = GardenBot()


def can_use_test(ctx: commands.Context) -> bool:
    if not isinstance(ctx.channel, discord.abc.GuildChannel) or not is_allowed_channel(
        ctx.channel
    ):
        return False
    if not isinstance(ctx.author, discord.Member):
        return False
    wanted = {value.strip().lower() for value in RESERVE_MANAGER_ROLE.split(",")}
    if str(ctx.author.id) in wanted:
        return True
    return any(
        str(role.id) in wanted or role.name.lower() in wanted for role in ctx.author.roles
    )


@bot.command(name="test")
@commands.check(can_use_test)
async def test(ctx: commands.Context) -> None:
    await bot.spawn_pokeball(ctx.channel)


@test.error
async def test_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if not isinstance(error, commands.CheckFailure):
        raise error
    await ctx.send("You are not allowed to use v.test here.", delete_after=10)


bot.run(DISCORD_TOKEN)