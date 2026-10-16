import asyncio
import io
import json
import re
from pathlib import Path

import discord
from PIL import Image

MENTION_PATTERN = re.compile(r"<@!?\d+>")
BODY_DIR = Path(__file__).parent / "assets" / "bodies"
SKIN_DIR = Path(__file__).parent / "assets" / "skincolors"
EYES_DIR = Path(__file__).parent / "assets" / "eyes"
BROWS_DIR = Path(__file__).parent / "assets" / "brows"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
EYE_PALETTES = json.loads(
    (Path(__file__).parent / "assets" / "eye_colors.json").read_text()
)
BASE_EYE_SHADES = [tuple(shade) + (255,) for shade in EYE_PALETTES[0]["shades"]]


def render_eye_preview(
    skin_path: Path,
    eye_path: Path,
    color_id: int,
    brow_path: Path | None = None,
) -> io.BytesIO:
    skin = Image.open(skin_path).convert("RGBA")
    eyes = Image.open(eye_path).convert("RGBA")
    eye_match = re.fullmatch(r"(\d+)\.eyeskin1", eye_path.stem, re.IGNORECASE)
    if eye_match is None:
        raise ValueError(f"Unexpected eye asset name: {eye_path.name}")
    reference_path = SKIN_DIR / f"{eye_match.group(1)}.skincolor1.png"
    reference = Image.open(reference_path).convert("RGBA")
    if skin.size != eyes.size or eyes.size != reference.size:
        raise ValueError("Skin, eye, and reference images must have the same dimensions.")

    target_shades = EYE_PALETTES[color_id - 1]["shades"]
    shade_map = {
        source: tuple(max(0, min(255, channel)) for channel in target) + (255,)
        for source, target in zip(BASE_EYE_SHADES, target_shades)
    }
    skin_pixels = skin.load()
    eye_pixels = eyes.load()
    reference_pixels = reference.load()
    for y in range(85, min(146, skin.height)):
        for x in range(skin.width):
            eye_pixel = eye_pixels[x, y]
            if eye_pixel != reference_pixels[x, y]:
                skin_pixels[x, y] = shade_map.get(eye_pixel, eye_pixel)

    if brow_path is not None:
        brows = Image.open(brow_path).convert("RGBA")
        brows = brows.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(brows)

    output = io.BytesIO()
    skin.save(output, format="PNG")
    output.seek(0)
    return output


class CategoryButton(discord.ui.Button):
    def __init__(
        self, name: str, row: int, stage: str, selected: bool = False
    ) -> None:
        super().__init__(
            label=name,
            style=discord.ButtonStyle.primary if selected else discord.ButtonStyle.secondary,
            row=row,
        )
        self.stage = stage

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.select_stage(interaction, self.stage)


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
    if not SKIN_DIR.is_dir():
        return []
    return sorted(
        (
            p
            for p in SKIN_DIR.iterdir()
            if re.fullmatch(
                rf"{re.escape(face_name)}\.skincolor\d+", p.stem, re.IGNORECASE
            )
            and p.suffix.lower() in IMAGE_SUFFIXES
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


def load_brow_images() -> list[Path]:
    if not BROWS_DIR.is_dir():
        return []
    return sorted(
        (path for path in BROWS_DIR.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


class BodyView(discord.ui.View):
    def __init__(self, owner_id: int, images: list[Path]) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.images = images
        self.index = 0
        self.step_images: dict[str, list[Path]] = {"shape": images}
        self.step_indices: dict[str, int] = {"shape": 0}
        self.message: discord.Message | None = None
        self.colors: "ColorView | None" = None
        self.stage = "shape"
        self.selected_face: str | None = None
        self.selected_skin_image: Path | None = None
        self.eye_color_id = 1
        self.selected_eye_image: Path | None = None
        self.eyes_button: CategoryButton | None = None
        self.brows_button: CategoryButton | None = None
        self.shape_button = CategoryButton("Shape", row=1, stage="shape", selected=True)
        self.done_button = DoneButton("Shape Done", row=1)
        self.add_item(self.shape_button)
        self.add_item(self.done_button)

    def current(self) -> discord.File:
        path = self.images[self.index]
        kind = {
            "shape": "Face",
            "skin": "Skin Color",
            "eyes": "Eyes",
            "eye_color": "Eye Color",
            "brows": "Brows",
        }[self.stage]
        if self.stage == "eye_color":
            label_index = self.eye_color_id
        elif self.stage == "brows":
            label_index = self.index
        else:
            label_index = self.index + 1
        self.face.label = f"{kind} {label_index}"
        if self.stage in {"eyes", "eye_color", "brows"} and self.selected_skin_image:
            eye_path = path if self.stage == "eyes" else self.selected_eye_image
            brow_path = path if self.stage == "brows" else None
            preview = render_eye_preview(
                self.selected_skin_image,
                eye_path,
                self.eye_color_id,
                brow_path,
            )
            return discord.File(preview, filename="character.png")
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
        if self.stage != "eye_color":
            self.step_indices[self.stage] = self.index
        if self.stage == "skin":
            self.selected_skin_image = self.images[self.index]
        elif self.stage == "eyes":
            self.selected_eye_image = self.images[self.index]
        file = self.current()
        await interaction.response.edit_message(attachments=[file], view=self)

    def update_stage_buttons(self) -> None:
        category_buttons = {
            "shape": self.shape_button,
            "eyes": self.eyes_button,
            "brows": self.brows_button,
        }
        for stage, button in category_buttons.items():
            if button is not None:
                button.style = (
                    discord.ButtonStyle.primary
                    if stage == self.stage
                    else discord.ButtonStyle.secondary
                )
                button.disabled = False

        self.done_button.label = {
            "shape": "Shape Done",
            "skin": "Skin Color Done",
            "eyes": "Eyes Done",
            "eye_color": "Eye Color Done",
            "brows": "Brows Done",
        }[self.stage]

    def add_step_button(self, button: CategoryButton) -> None:
        self.remove_item(self.done_button)
        self.add_item(button)
        self.add_item(self.done_button)

    async def select_stage(
        self,
        interaction: discord.Interaction,
        stage: str,
        from_color_view: bool = False,
    ) -> None:
        image_stage = "eyes" if stage == "eye_color" else stage
        images = self.step_images.get(image_stage, [])
        if not images:
            await interaction.response.send_message(
                f"{stage.replace('_', ' ').title()} is not available yet.",
                ephemeral=True,
            )
            return

        if self.stage != "eye_color":
            self.step_indices[self.stage] = self.index
        if self.stage == "skin":
            self.selected_skin_image = self.images[self.index]
        elif self.stage == "eyes":
            self.selected_eye_image = self.images[self.index]

        self.stage = stage
        self.images = images
        self.index = self.step_indices.get(image_stage, 0)
        if stage == "skin":
            self.selected_skin_image = self.images[self.index]
        elif stage in {"eye_color", "brows"}:
            self.selected_eye_image = self.step_images["eyes"][
                self.step_indices.get("eyes", 0)
            ]
        self.update_stage_buttons()
        preview = self.current()

        if from_color_view:
            await interaction.response.defer()
            if self.message is not None:
                await self.message.edit(attachments=[preview], view=self)
        else:
            await interaction.response.edit_message(attachments=[preview], view=self)

        if self.colors is not None and self.colors.message is not None:
            self.colors.update_stage_buttons(self.stage, self.step_images)
            await self.colors.message.edit(view=self.colors)

    async def finish_step(self, interaction: discord.Interaction) -> None:
        if self.stage == "shape":
            await self.finish_shape(interaction)
        elif self.stage == "skin":
            await self.finish_skin(interaction)
        elif self.stage == "eyes":
            await self.finish_eyes(interaction)
        elif self.stage == "eye_color":
            await self.finish_eye_color(interaction)
        elif self.stage == "brows":
            await interaction.response.send_message("Your character is ready!", ephemeral=True)

    async def finish_shape(self, interaction: discord.Interaction) -> None:
        face_name = self.images[self.index].stem
        shape_changed = self.selected_face != face_name
        self.selected_face = face_name
        skin_images = load_skin_images(face_name)
        if not skin_images:
            await interaction.response.send_message(
                f"No skin color images for face {face_name} yet.", ephemeral=True
            )
            return

        self.step_images["skin"] = skin_images
        if shape_changed:
            self.step_indices["skin"] = 0
        if self.colors is not None:
            self.colors.update_stage_buttons("shape", self.step_images)
        await self.select_stage(interaction, "skin")

    async def finish_skin(self, interaction: discord.Interaction) -> None:
        self.selected_skin_image = self.images[self.index]
        eye_images = load_eye_images()
        if not eye_images:
            await interaction.response.send_message(
                "No eye images found in assets/eyes yet.", ephemeral=True
            )
            return

        self.step_images["eyes"] = eye_images
        self.step_indices.setdefault("eyes", 0)
        if self.eyes_button is None:
            self.eyes_button = CategoryButton("Eyes", row=1, stage="eyes")
            self.add_step_button(self.eyes_button)
        await self.select_stage(interaction, "eyes")

    async def finish_eyes(self, interaction: discord.Interaction) -> None:
        self.selected_eye_image = self.images[self.index]
        self.step_indices["eyes"] = self.index
        if self.colors is not None:
            self.colors.add_eye_color_button()
        await self.select_stage(interaction, "eye_color")

    async def finish_eye_color(self, interaction: discord.Interaction) -> None:
        brow_images = load_brow_images()
        if not brow_images:
            await interaction.response.send_message(
                "No brow images found in assets/brows.", ephemeral=True
            )
            return

        self.step_images["brows"] = brow_images
        self.step_indices.setdefault("brows", 0)
        if self.brows_button is None:
            self.brows_button = CategoryButton("Brows", row=1, stage="brows")
            self.add_step_button(self.brows_button)
        if self.colors is not None:
            self.colors.add_brows_button()
        await self.select_stage(interaction, "brows")

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.stage == "eye_color":
            self.eye_color_id = (self.eye_color_id - 2) % len(EYE_PALETTES) + 1
        else:
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
        if self.stage == "eye_color":
            self.eye_color_id = self.eye_color_id % len(EYE_PALETTES) + 1
        else:
            self.index = (self.index + 1) % len(self.images)
        await self.show(interaction)


class ColorButton(discord.ui.Button):
    def __init__(self, name: str, stage: str, row: int) -> None:
        super().__init__(label=name, style=discord.ButtonStyle.success, row=row)
        self.stage = stage

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.body_view.select_stage(
            interaction, self.stage, from_color_view=True
        )


class ColorView(discord.ui.View):
    def __init__(self, owner_id: int, body_view: BodyView) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.body_view = body_view
        self.message: discord.Message | None = None
        self.skin_button = ColorButton("Skin Color", "skin", row=0)
        self.eye_color_button: ColorButton | None = None
        self.brows_button: ColorButton | None = None
        self.skin_button.disabled = True
        self.add_item(self.skin_button)

    def add_eye_color_button(self) -> None:
        if self.eye_color_button is not None:
            return
        self.eye_color_button = ColorButton("Eye Color", "eye_color", row=0)
        self.eye_color_button.disabled = True
        self.add_item(self.eye_color_button)

    def add_brows_button(self) -> None:
        if self.brows_button is not None:
            return
        self.brows_button = ColorButton("Brows", "brows", row=0)
        self.brows_button.disabled = True
        self.add_item(self.brows_button)

    def update_stage_buttons(
        self, selected_stage: str, available_images: dict[str, list[Path]]
    ) -> None:
        buttons = {
            "skin": self.skin_button,
            "eye_color": self.eye_color_button,
            "brows": self.brows_button,
        }
        for stage, button in buttons.items():
            if button is None:
                continue
            image_stage = "eyes" if stage == "eye_color" else stage
            available = bool(available_images.get(image_stage))
            button.disabled = not available
            button.style = (
                discord.ButtonStyle.primary
                if stage == selected_stage
                else discord.ButtonStyle.success
            )

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

        colors = ColorView(self.owner_id, view)
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
