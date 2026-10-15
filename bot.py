import asyncio
import re
from pathlib import Path

import discord

MENTION_PATTERN = re.compile(r"<@!?\d+>")
BODY_DIR = Path(__file__).parent / "assets" / "bodies"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
CATEGORIES = [
    "Shape", "Eyes", "Brows", "Nose", "Mouth", "Hair", "Bangs", "Mark1", "Mark2",
    "Facial Hair", "Shirt", "Sleeve", "Top", "Special", "Acc1", "Acc2", "Hat",
]
SELECTED_CATEGORY = "Shape"


class CategoryButton(discord.ui.Button):
    def __init__(self, name: str, row: int) -> None:
        selected = name == SELECTED_CATEGORY
        super().__init__(
            label=name,
            style=discord.ButtonStyle.primary if selected else discord.ButtonStyle.secondary,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.label == SELECTED_CATEGORY:
            await interaction.response.defer()
        else:
            await interaction.response.send_message(
                f"{self.label} is not available yet.", ephemeral=True
            )


def natural_key(path: Path) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name.lower())]


def load_body_images() -> list[Path]:
    if not BODY_DIR.is_dir():
        return []
    return sorted(
        (p for p in BODY_DIR.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


class BodyView(discord.ui.View):
    def __init__(self, owner_id: int, images: list[Path]) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.images = images
        self.index = 0
        self.message: discord.Message | None = None
        for position, name in enumerate(CATEGORIES):
            self.add_item(CategoryButton(name, row=1 + position // 5))

    def current(self) -> discord.File:
        path = self.images[self.index]
        self.face.label = f"Face {self.index + 1}"
        return discord.File(path, filename=f"body{path.suffix.lower()}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This is not your farm.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.message is not None:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

    async def show(self, interaction: discord.Interaction) -> None:
        file = self.current()
        await interaction.response.edit_message(attachments=[file], view=self)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.index = (self.index - 1) % len(self.images)
        await self.show(interaction)

    @discord.ui.button(
        label="Face 1", style=discord.ButtonStyle.secondary, disabled=True, row=0
    )
    async def face(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        pass

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary, row=0)
    async def next(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.index = (self.index + 1) % len(self.images)
        await self.show(interaction)


class StartView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=60)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This question is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(view=None)
        reply = await interaction.message.reply("First we are going to make you!")
        self.stop()

        await asyncio.sleep(3)
        await reply.delete()

        images = load_body_images()
        if not images:
            await interaction.message.reply("No body images found in assets/bodies.")
            return
        view = BodyView(self.owner_id, images)
        file = view.current()
        view.message = await interaction.message.reply(file=file, view=view)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(view=None)
        await interaction.message.reply("Okay, maybe later.")
        self.stop()


class FarmBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.user not in message.mentions:
            return

        text = MENTION_PATTERN.sub("", message.content).strip().lower()
        if text == "start":
            await message.reply(
                "Do you want to start your farm?", view=StartView(message.author.id)
            )
