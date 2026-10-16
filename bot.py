import asyncio
import re
from pathlib import Path

import discord

MENTION_PATTERN = re.compile(r"<@!?\d+>")
BODY_DIR = Path(__file__).parent / "assets" / "bodies"
SKIN_DIR = Path(__file__).parent / "assets" / "skincolors"
EYES_DIR = Path(__file__).parent / "assets" / "eyes"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
class CategoryButton(discord.ui.Button):
    def __init__(self, name: str, row: int, selected: bool = False) -> None:
        super().__init__(
            label=name,
            style=discord.ButtonStyle.primary if selected else discord.ButtonStyle.secondary,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class DoneButton(discord.ui.Button):
    def __init__(self, label: str, row: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.finish_step(interaction)


def natural_key(path: Path) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name.lower())]


def load_body_images() -> list[Path]:
    if not BODY_DIR.is_dir():
        return []
    return sorted(
        (p for p in BODY_DIR.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


def load_skin_images(face_name: str) -> list[Path]:
    # Files are named like 7.skincolor1.png for face 7.
    if not SKIN_DIR.is_dir():
        return []
    prefix = f"{face_name}.skincolor".lower()
    return sorted(
        (
            p
            for p in SKIN_DIR.iterdir()
            if p.name.lower().startswith(prefix) and p.suffix.lower() in IMAGE_SUFFIXES
        ),
        key=natural_key,
    )


def load_eye_images() -> list[Path]:
    if not EYES_DIR.is_dir():
        return []
    return sorted(
        (
            p
            for p in EYES_DIR.iterdir()
            if re.fullmatch(r"\d+\.eyeskin1", p.stem.lower())
            and p.suffix.lower() in IMAGE_SUFFIXES
        ),
        key=natural_key,
    )


class BodyView(discord.ui.View):
    def __init__(self, owner_id: int, images: list[Path]) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.images = images
        self.index = 0
        self.message: discord.Message | None = None
        self.colors: "ColorView | None" = None
        self.stage = "shape"
        self.selected_face: str | None = None
        self.eyes_button: CategoryButton | None = None
        self.shape_button = CategoryButton("Shape", row=1, selected=True)
        self.done_button = DoneButton("Shape Done", row=1)
        self.add_item(self.shape_button)
        self.add_item(self.done_button)

    def current(self) -> discord.File:
        path = self.images[self.index]
        kind = {"shape": "Face", "skin": "Skin Color", "eyes": "Eyes"}[self.stage]
        self.face.label = f"{kind} {self.index + 1}"
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

    async def finish_step(self, interaction: discord.Interaction) -> None:
        if self.stage == "skin":
            await self.finish_skin(interaction)
            return
        if self.stage == "eyes":
            await self.finish_eyes(interaction)
            return
        if self.stage != "shape":
            await interaction.response.send_message(
                "The next step is not available yet.", ephemeral=True
            )
            return

        self.stage = "skin"
        face_name = self.images[self.index].stem
        self.selected_face = face_name
        skin_images = load_skin_images(face_name)
        self.shape_button.style = discord.ButtonStyle.secondary
        self.shape_button.disabled = True
        self.done_button.label = "Skin Color Done"
        if skin_images:
            self.images = skin_images
            self.index = 0
            file = self.current()
            await interaction.response.edit_message(attachments=[file], view=self)
        else:
            self.previous.disabled = True
            self.next.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"No skin color images for face {face_name} yet.", ephemeral=True
            )

        if self.colors is not None and self.colors.message is not None:
            self.colors.skin_button.style = discord.ButtonStyle.primary
            await self.colors.message.edit(view=self.colors)

    async def finish_skin(self, interaction: discord.Interaction) -> None:
        self.stage = "eyes"
        eye_images = load_eye_images()

        # Rebuild the row so the order is Shape, Eyes, Eyes Done.
        self.remove_item(self.done_button)
        self.eyes_button = CategoryButton("Eyes", row=1, selected=True)
        self.add_item(self.eyes_button)
        self.done_button = DoneButton("Eyes Done", row=1)
        self.add_item(self.done_button)
        if eye_images:
            self.images = eye_images
            self.index = 0
            self.previous.disabled = False
            self.next.disabled = False
            await interaction.response.edit_message(
                attachments=[self.current()], view=self
            )
        else:
            self.previous.disabled = True
            self.next.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                "No eye images found in assets/eyes yet.", ephemeral=True
            )

        if self.colors is not None and self.colors.message is not None:
            self.colors.skin_button.style = discord.ButtonStyle.secondary
            self.colors.skin_button.disabled = True
            await self.colors.message.edit(view=self.colors)

    async def finish_eyes(self, interaction: discord.Interaction) -> None:
        self.stage = "eye_color"
        self.previous.disabled = True
        self.next.disabled = True
        if self.eyes_button is not None:
            self.eyes_button.style = discord.ButtonStyle.secondary
            self.eyes_button.disabled = True
        self.done_button.label = "Eye Color Done"
        await interaction.response.edit_message(view=self)

        if self.colors is not None and self.colors.message is not None:
            self.colors.add_eye_color_button()
            await self.colors.message.edit(view=self.colors)

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


class ColorButton(discord.ui.Button):
    def __init__(self, name: str, row: int) -> None:
        super().__init__(label=name, style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.style == discord.ButtonStyle.primary:
            await interaction.response.defer()
        else:
            await interaction.response.send_message(
                f"{self.label} is not available yet.", ephemeral=True
            )


class ColorView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.message: discord.Message | None = None
        self.skin_button = ColorButton("Skin Color", row=0)
        self.eye_color_button: ColorButton | None = None
        self.add_item(self.skin_button)

    def add_eye_color_button(self) -> None:
        if self.eye_color_button is not None:
            return
        self.eye_color_button = ColorButton("Eye Color", row=0)
        self.eye_color_button.style = discord.ButtonStyle.primary
        self.add_item(self.eye_color_button)

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
        await interaction.response.edit_message(
            content="First we are going to create your character!", view=None
        )
        self.stop()

        await asyncio.sleep(3)

        images = load_body_images()
        if not images:
            await interaction.message.edit(
                content="No body images found in assets/bodies."
            )
            return
        view = BodyView(self.owner_id, images)
        file = view.current()
        view.message = await interaction.message.edit(
            content=None, attachments=[file], view=view
        )

        colors = ColorView(self.owner_id)
        colors.message = await view.message.reply("Colors", view=colors)
        view.colors = colors

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
