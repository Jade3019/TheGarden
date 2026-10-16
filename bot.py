import asyncio
import io
import json
import os
import re
from pathlib import Path

import discord
from PIL import Image

MENTION_PATTERN = re.compile(r"<@!?\d+>")
BODY_DIR = Path(__file__).parent / "assets" / "bodies"
SKIN_DIR = Path(__file__).parent / "assets" / "skincolors"
EYES_DIR = Path(__file__).parent / "assets" / "eyes"
BROWS_DIR = Path(__file__).parent / "assets" / "brows"
NOSES_DIR = Path(__file__).parent / "assets" / "noses"
MOUTHS_DIR = Path(__file__).parent / "assets" / "mouths"
HAIR_DIR = Path(__file__).parent / "assets" / "hair"
BANGS_TOP_DIR = Path(__file__).parent / "assets" / "bangs" / "top"
BANGS_BOTTOM_DIR = Path(__file__).parent / "assets" / "bangs" / "bottom"
PROGRESS_FILE = Path(__file__).parent / "data" / "farm_progress.json"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
EYE_PALETTES = json.loads(
    (Path(__file__).parent / "assets" / "eye_colors.json").read_text()
)
BASE_EYE_SHADES = [tuple(shade) + (255,) for shade in EYE_PALETTES[0]["shades"]]
HAIR_PALETTES = json.loads(
    (Path(__file__).parent / "assets" / "hair_colors.json").read_text()
)
BASE_HAIR_SHADES = [tuple(shade) for shade in HAIR_PALETTES[0]["shades"]]


def read_progress(user_id: int) -> dict | None:
    try:
        data = json.loads(PROGRESS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data.get(str(user_id))


def write_progress(user_id: int, progress: dict) -> None:
    try:
        data = json.loads(PROGRESS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    data[str(user_id)] = progress
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = PROGRESS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, separators=(",", ":")))
    os.replace(temporary, PROGRESS_FILE)


def recolor_hair_layer(path: Path, color_id: int) -> Image.Image:
    layer = Image.open(path).convert("RGBA")
    target_shades = HAIR_PALETTES[color_id - 1]["shades"]
    shade_map = {
        source: tuple(max(0, min(255, channel)) for channel in target) + (255,)
        for source, target in zip(BASE_HAIR_SHADES, target_shades)
    }
    pixels = layer.load()
    for y in range(layer.height):
        for x in range(layer.width):
            pixel = pixels[x, y]
            replacement = shade_map.get(pixel[:3])
            if replacement is not None:
                pixels[x, y] = replacement[:3] + (pixel[3],)
    return layer


def render_eye_preview(
    skin_path: Path,
    eye_path: Path,
    color_id: int,
    brow_path: Path | None = None,
    nose_path: Path | None = None,
    mouth_path: Path | None = None,
    hair_path: Path | None = None,
    bangs_top_path: Path | None = None,
    bangs_bottom_path: Path | None = None,
    hair_color_id: int = 1,
) -> io.BytesIO:
    skin = Image.open(skin_path).convert("RGBA")
    back_layers = [layer for layer in (hair_path, bangs_bottom_path) if layer is not None]
    if back_layers:
        body = skin.copy()
        body_pixels = body.load()
        for y in range(body.height):
            for x in range(body.width):
                red, green, blue, _ = body_pixels[x, y]
                if red >= 254 and green >= 254 and blue >= 254:
                    body_pixels[x, y] = (255, 255, 255, 0)
        background = Image.new("RGBA", skin.size, (255, 255, 255, 255))
        for layer_path in back_layers:
            layer = recolor_hair_layer(layer_path, hair_color_id)
            layer = layer.resize(skin.size, Image.Resampling.NEAREST)
            background.alpha_composite(layer)
        background.alpha_composite(body)
        skin = background
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
    if nose_path is not None:
        nose = Image.open(nose_path).convert("RGBA")
        nose = nose.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(nose)
    if mouth_path is not None:
        mouth = Image.open(mouth_path).convert("RGBA")
        mouth = mouth.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(mouth)
    if bangs_top_path is not None:
        bangs_top = recolor_hair_layer(bangs_top_path, hair_color_id)
        bangs_top = bangs_top.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(bangs_top)

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


def load_nose_images() -> list[Path]:
    if not NOSES_DIR.is_dir():
        return []
    return sorted(
        (path for path in NOSES_DIR.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


def load_mouth_images() -> list[Path]:
    if not MOUTHS_DIR.is_dir():
        return []
    return sorted(
        (path for path in MOUTHS_DIR.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


def load_hair_images() -> list[Path]:
    if not HAIR_DIR.is_dir():
        return []
    return sorted(
        (path for path in HAIR_DIR.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


def load_bang_images() -> list[Path]:
    if not BANGS_TOP_DIR.is_dir() or not BANGS_BOTTOM_DIR.is_dir():
        return []
    return sorted(
        (
            top_path
            for top_path in BANGS_TOP_DIR.iterdir()
            if top_path.suffix.lower() in IMAGE_SUFFIXES
            and (BANGS_BOTTOM_DIR / top_path.name).is_file()
        ),
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
        self.selected_brow_image: Path | None = None
        self.selected_nose_image: Path | None = None
        self.selected_mouth_image: Path | None = None
        self.selected_hair_image: Path | None = None
        self.selected_bangs_top_image: Path | None = None
        self.selected_bangs_bottom_image: Path | None = None
        self.hair_color_id = 1
        self.eyes_button: CategoryButton | None = None
        self.brows_button: CategoryButton | None = None
        self.nose_button: CategoryButton | None = None
        self.mouth_button: CategoryButton | None = None
        self.hair_button: CategoryButton | None = None
        self.bangs_button: CategoryButton | None = None
        self.shape_button = CategoryButton("Shape", row=1, stage="shape", selected=True)
        self.done_button = DoneButton("Shape Done", row=1)
        self.add_item(self.shape_button)
        self.add_item(self.done_button)

    @classmethod
    def restore(cls, owner_id: int, saved: dict) -> "BodyView | None":
        shape_images = load_body_images()
        if not shape_images:
            return None
        view = cls(owner_id, shape_images)
        view.selected_face = saved.get("selected_face")
        view.eye_color_id = int(saved.get("eye_color_id", 1))
        view.hair_color_id = int(saved.get("hair_color_id", 1))
        view.step_indices.update(
            {key: max(0, int(value)) for key, value in saved.get("step_indices", {}).items()}
        )

        loaders = {
            "skin": lambda: load_skin_images(view.selected_face or ""),
            "eyes": load_eye_images,
            "brows": load_brow_images,
            "nose": load_nose_images,
            "mouth": load_mouth_images,
            "hair": load_hair_images,
            "bangs": load_bang_images,
        }
        for step in saved.get("steps", []):
            if step in loaders:
                images = loaders[step]()
                if images:
                    view.step_images[step] = images

        saved_stage = saved.get("stage", "shape")
        image_stage = {"eye_color": "eyes", "hair_color": "bangs"}.get(
            saved_stage, saved_stage
        )
        if image_stage not in view.step_images:
            saved_stage = "shape"
            image_stage = "shape"
        view.stage = saved_stage
        view.images = view.step_images[image_stage]
        view.index = min(
            view.step_indices.get(image_stage, 0), len(view.images) - 1
        )

        for key, attribute in (
            ("skin", "selected_skin_image"),
            ("eyes", "selected_eye_image"),
            ("brows", "selected_brow_image"),
            ("nose", "selected_nose_image"),
            ("mouth", "selected_mouth_image"),
            ("hair", "selected_hair_image"),
        ):
            images = view.step_images.get(key)
            if images:
                selected_index = min(view.step_indices.get(key, 0), len(images) - 1)
                setattr(view, attribute, images[selected_index])

        bangs = view.step_images.get("bangs")
        if bangs:
            bangs_index = min(view.step_indices.get("bangs", 0), len(bangs) - 1)
            view.selected_bangs_top_image = bangs[bangs_index]
            view.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / bangs[bangs_index].name

        for step, label in (
            ("eyes", "Eyes"),
            ("brows", "Brows"),
            ("nose", "Nose"),
            ("mouth", "Mouth"),
            ("hair", "Hair"),
            ("bangs", "Bangs"),
        ):
            if step in view.step_images:
                button = CategoryButton(label, row=1, stage=step)
                setattr(view, f"{step}_button", button)
                view.add_step_button(button)
        view.update_stage_buttons()
        return view

    def save_progress(self) -> None:
        if self.stage not in {"eye_color", "hair_color"}:
            self.step_indices[self.stage] = self.index
        if self.stage == "skin":
            self.selected_skin_image = self.images[self.index]
        elif self.stage == "eyes":
            self.selected_eye_image = self.images[self.index]
        elif self.stage == "brows":
            self.selected_brow_image = self.images[self.index]
        elif self.stage == "nose":
            self.selected_nose_image = self.images[self.index]
        elif self.stage == "mouth":
            self.selected_mouth_image = self.images[self.index]
        elif self.stage == "hair":
            self.selected_hair_image = self.images[self.index]
        elif self.stage == "bangs":
            self.selected_bangs_top_image = self.images[self.index]
            self.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / self.images[self.index].name

        write_progress(
            self.owner_id,
            {
                "stage": self.stage,
                "selected_face": self.selected_face,
                "step_indices": self.step_indices,
                "steps": list(self.step_images),
                "eye_color_id": self.eye_color_id,
                "hair_color_id": self.hair_color_id,
            },
        )

    def current(self) -> discord.File:
        path = self.images[self.index]
        kind = {
            "shape": "Face",
            "skin": "Skin Color",
            "eyes": "Eyes",
            "eye_color": "Eye Color",
            "brows": "Brows",
            "nose": "Nose",
            "mouth": "Mouth",
            "hair": "Hair",
            "bangs": "Bangs",
            "hair_color": "Hair Color",
        }[self.stage]
        if self.stage == "eye_color":
            label_index = self.eye_color_id
        elif self.stage == "hair_color":
            label_index = self.hair_color_id
        elif self.stage == "brows":
            label_index = self.index
        elif self.stage in {"nose", "mouth", "hair", "bangs"}:
            label_index = self.index
        else:
            label_index = self.index + 1
        self.face.label = f"{kind} {label_index}"
        if self.stage in {"eyes", "eye_color", "brows", "nose", "mouth", "hair", "bangs", "hair_color"} and self.selected_skin_image:
            eye_path = path if self.stage == "eyes" else self.selected_eye_image
            brow_path = path if self.stage == "brows" else self.selected_brow_image
            nose_path = path if self.stage == "nose" else self.selected_nose_image
            mouth_path = path if self.stage == "mouth" else self.selected_mouth_image
            hair_path = path if self.stage == "hair" else self.selected_hair_image
            bangs_top_path = path if self.stage == "bangs" else self.selected_bangs_top_image
            bangs_bottom_path = (
                BANGS_BOTTOM_DIR / path.name
                if self.stage == "bangs"
                else self.selected_bangs_bottom_image
            )
            preview = render_eye_preview(
                self.selected_skin_image,
                eye_path,
                self.eye_color_id,
                brow_path,
                nose_path,
                mouth_path,
                hair_path,
                bangs_top_path,
                bangs_bottom_path,
                self.hair_color_id,
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
        self.save_progress()
        file = self.current()
        await interaction.response.edit_message(attachments=[file], view=self)

    def update_stage_buttons(self) -> None:
        category_buttons = {
            "shape": self.shape_button,
            "eyes": self.eyes_button,
            "brows": self.brows_button,
            "nose": self.nose_button,
            "mouth": self.mouth_button,
            "hair": self.hair_button,
            "bangs": self.bangs_button,
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
            "nose": "Nose Done",
            "mouth": "Mouth Done",
            "hair": "Hair Done",
            "bangs": "Bangs Done",
            "hair_color": "Hair Color Done",
        }[self.stage]

    def add_step_button(self, button: CategoryButton) -> None:
        self.remove_item(self.done_button)
        for row in range(button.row, 5):
            category_count = sum(
                1
                for item in self.children
                if isinstance(item, CategoryButton) and item.row == row
            )
            if category_count < 5:
                button.row = row
                break
        self.add_item(button)
        category_rows = [
            item.row
            for item in self.children
            if isinstance(item, CategoryButton)
        ]
        done_row = max(category_rows)
        if sum(row == done_row for row in category_rows) >= 5:
            done_row += 1
        self.done_button.row = done_row
        self.add_item(self.done_button)

    async def select_stage(
        self,
        interaction: discord.Interaction,
        stage: str,
        from_color_view: bool = False,
    ) -> None:
        image_stage = {
            "eye_color": "eyes",
            "hair_color": "bangs",
        }.get(stage, stage)
        images = self.step_images.get(image_stage, [])
        if not images:
            await interaction.response.send_message(
                f"{stage.replace('_', ' ').title()} is not available yet.",
                ephemeral=True,
            )
            return

        if self.stage not in {"eye_color", "hair_color"}:
            self.step_indices[self.stage] = self.index
        if self.stage == "skin":
            self.selected_skin_image = self.images[self.index]
        elif self.stage == "eyes":
            self.selected_eye_image = self.images[self.index]
        elif self.stage == "brows":
            self.selected_brow_image = self.images[self.index]
        elif self.stage == "nose":
            self.selected_nose_image = self.images[self.index]
        elif self.stage == "mouth":
            self.selected_mouth_image = self.images[self.index]
        elif self.stage == "hair":
            self.selected_hair_image = self.images[self.index]
        elif self.stage == "bangs":
            self.selected_bangs_top_image = self.images[self.index]
            self.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / self.images[self.index].name
        elif self.stage == "hair_color":
            self.selected_bangs_top_image = self.step_images["bangs"][
                self.step_indices.get("bangs", 0)
            ]
            self.selected_bangs_bottom_image = (
                BANGS_BOTTOM_DIR / self.selected_bangs_top_image.name
            )

        self.stage = stage
        self.images = images
        self.index = self.step_indices.get(image_stage, 0)
        if stage == "skin":
            self.selected_skin_image = self.images[self.index]
        elif stage in {"eye_color", "brows"}:
            self.selected_eye_image = self.step_images["eyes"][
                self.step_indices.get("eyes", 0)
            ]
        if stage == "brows":
            self.selected_brow_image = self.images[self.index]
        elif stage == "nose":
            self.selected_nose_image = self.images[self.index]
        elif stage == "mouth":
            self.selected_mouth_image = self.images[self.index]
        elif stage == "hair":
            self.selected_hair_image = self.images[self.index]
        elif stage == "bangs":
            self.selected_bangs_top_image = self.images[self.index]
            self.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / self.images[self.index].name
        elif stage == "hair_color":
            self.selected_hair_image = self.step_images["hair"][
                self.step_indices.get("hair", 0)
            ]
            self.selected_bangs_top_image = self.images[self.index]
            self.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / self.images[self.index].name
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
        self.save_progress()

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
            await self.finish_brows(interaction)
        elif self.stage == "nose":
            await self.finish_nose(interaction)
        elif self.stage == "mouth":
            await self.finish_mouth(interaction)
        elif self.stage == "hair":
            await self.finish_hair(interaction)
        elif self.stage == "bangs":
            await self.finish_bangs(interaction)
        elif self.stage == "hair_color":
            await interaction.response.send_message(
                "Your character is ready!", ephemeral=True
            )

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
        await self.select_stage(interaction, "brows")

    async def finish_brows(self, interaction: discord.Interaction) -> None:
        self.selected_brow_image = self.images[self.index]
        self.step_indices["brows"] = self.index
        nose_images = load_nose_images()
        if not nose_images:
            await interaction.response.send_message(
                "No nose images found in assets/noses.", ephemeral=True
            )
            return

        self.step_images["nose"] = nose_images
        self.step_indices.setdefault("nose", 0)
        if self.nose_button is None:
            self.nose_button = CategoryButton("Nose", row=1, stage="nose")
            self.add_step_button(self.nose_button)
        await self.select_stage(interaction, "nose")

    async def finish_nose(self, interaction: discord.Interaction) -> None:
        self.selected_nose_image = self.images[self.index]
        self.step_indices["nose"] = self.index
        mouth_images = load_mouth_images()
        if not mouth_images:
            await interaction.response.send_message(
                "No mouth images found in assets/mouths.", ephemeral=True
            )
            return

        self.step_images["mouth"] = mouth_images
        self.step_indices.setdefault("mouth", 0)
        if self.mouth_button is None:
            self.mouth_button = CategoryButton("Mouth", row=1, stage="mouth")
            self.add_step_button(self.mouth_button)
        await self.select_stage(interaction, "mouth")

    async def finish_mouth(self, interaction: discord.Interaction) -> None:
        self.selected_mouth_image = self.images[self.index]
        self.step_indices["mouth"] = self.index
        hair_images = load_hair_images()
        bang_images = load_bang_images()
        if not hair_images:
            await interaction.response.send_message(
                "No hairstyle images found in assets/hair.", ephemeral=True
            )
            return

        self.step_images["hair"] = hair_images
        self.step_indices.setdefault("hair", 0)
        if bang_images:
            self.step_images["bangs"] = bang_images
            self.step_indices.setdefault("bangs", min(8, len(bang_images) - 1))
            selected_bangs = bang_images[self.step_indices["bangs"]]
            self.selected_bangs_top_image = selected_bangs
            self.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / selected_bangs.name
        if self.hair_button is None:
            self.hair_button = CategoryButton("Hair", row=1, stage="hair")
            self.add_step_button(self.hair_button)
        await self.select_stage(interaction, "hair")

    async def finish_hair(self, interaction: discord.Interaction) -> None:
        self.selected_hair_image = self.images[self.index]
        self.step_indices["hair"] = self.index
        bang_images = load_bang_images()
        if not bang_images:
            await interaction.response.send_message(
                "No bangs images found in assets/bangs.", ephemeral=True
            )
            return

        self.step_images["bangs"] = bang_images
        self.step_indices.setdefault("bangs", 0)
        if self.bangs_button is None:
            self.bangs_button = CategoryButton("Bangs", row=1, stage="bangs")
            self.add_step_button(self.bangs_button)
        await self.select_stage(interaction, "bangs")

    async def finish_bangs(self, interaction: discord.Interaction) -> None:
        self.selected_bangs_top_image = self.images[self.index]
        self.selected_bangs_bottom_image = BANGS_BOTTOM_DIR / self.images[self.index].name
        self.step_indices["bangs"] = self.index
        if self.colors is not None:
            self.colors.add_hair_color_button()
        await self.select_stage(interaction, "hair_color")

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.stage == "eye_color":
            self.eye_color_id = (self.eye_color_id - 2) % len(EYE_PALETTES) + 1
        elif self.stage == "hair_color":
            self.hair_color_id = (self.hair_color_id - 2) % len(HAIR_PALETTES) + 1
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
        elif self.stage == "hair_color":
            self.hair_color_id = self.hair_color_id % len(HAIR_PALETTES) + 1
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


class SaveProgressButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="Save", style=discord.ButtonStyle.danger, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.body_view.save_progress()
        await interaction.response.send_message("Progress saved.", ephemeral=True)


class ColorView(discord.ui.View):
    def __init__(self, owner_id: int, body_view: BodyView) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.body_view = body_view
        self.message: discord.Message | None = None
        self.skin_button = ColorButton("Skin Color", "skin", row=0)
        self.eye_color_button: ColorButton | None = None
        self.hair_color_button: ColorButton | None = None
        self.save_button = SaveProgressButton()
        self.skin_button.disabled = True
        self.add_item(self.skin_button)
        self.add_item(self.save_button)

    def add_before_save(self, button: discord.ui.Button) -> None:
        self.remove_item(self.save_button)
        self.add_item(button)
        self.add_item(self.save_button)

    def add_eye_color_button(self) -> None:
        if self.eye_color_button is not None:
            return
        self.eye_color_button = ColorButton("Eye Color", "eye_color", row=0)
        self.eye_color_button.disabled = True
        self.add_before_save(self.eye_color_button)

    def add_hair_color_button(self) -> None:
        if self.hair_color_button is not None:
            return
        self.hair_color_button = ColorButton("Hair Color", "hair_color", row=0)
        self.hair_color_button.disabled = True
        self.add_before_save(self.hair_color_button)

    def update_stage_buttons(
        self, selected_stage: str, available_images: dict[str, list[Path]]
    ) -> None:
        buttons = {
            "skin": self.skin_button,
            "eye_color": self.eye_color_button,
            "hair_color": self.hair_color_button,
        }
        for stage, button in buttons.items():
            if button is None:
                continue
            image_stage = {
                "eye_color": "eyes",
                "hair_color": "bangs",
            }.get(stage, stage)
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
        view.save_progress()

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
            saved = read_progress(message.author.id)
            if saved is not None:
                view = BodyView.restore(message.author.id, saved)
                if view is not None:
                    view.message = await message.reply(file=view.current(), view=view)
                    colors = ColorView(message.author.id, view)
                    if "eyes" in view.step_images:
                        colors.add_eye_color_button()
                    if "bangs" in view.step_images:
                        colors.add_hair_color_button()
                    colors.update_stage_buttons(view.stage, view.step_images)
                    colors.message = await view.message.reply("Colors", view=colors)
                    view.colors = colors
                    view.save_progress()
                    return
            await message.reply(
                "Do you want to start your farm?", view=StartView(message.author.id)
            )
