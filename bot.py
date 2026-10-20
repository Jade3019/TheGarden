import asyncio
import io
import json
import os
import re
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont
from arrival_scene import (
    JOURNEY_CHOICES,
    JOURNEY_QUESTION,
    HAPPY_LEWIS,
    NORMAL_LEWIS,
    SAD_LEWIS,
    dialogue_scene,
    play_arrival,
    play_farm_reveal,
)
from fishing_minigame import FishingVersionSelectView
from inventory_test import InventoryTestView
from main_menu import render_main_menu
MENTION_PATTERN = re.compile(r"<@!?\d+>")
BODY_DIR = Path(__file__).parent / "assets" / "bodies"
SKIN_DIR = Path(__file__).parent / "assets" / "skincolors"
MASCULINE_BODY_DIR = Path(__file__).parent / "assets" / "masculine" / "bodies"
MASCULINE_SKIN_DIR = Path(__file__).parent / "assets" / "masculine" / "skincolors"
EYES_DIR = Path(__file__).parent / "assets" / "eyes"
BROWS_DIR = Path(__file__).parent / "assets" / "brows"
NOSES_DIR = Path(__file__).parent / "assets" / "noses"
MOUTHS_DIR = Path(__file__).parent / "assets" / "mouths"
HAIR_DIR = Path(__file__).parent / "assets" / "hair"
BANGS_TOP_DIR = Path(__file__).parent / "assets" / "bangs" / "top"
BANGS_BOTTOM_DIR = Path(__file__).parent / "assets" / "bangs" / "bottom"
MARKS_TOP_DIR = Path(__file__).parent / "assets" / "marks" / "top"
MARKS_BOTTOM_DIR = Path(__file__).parent / "assets" / "marks" / "bottom"
PROGRESS_FILE = Path(__file__).parent / "data" / "farm_progress.json"
FARMS_DIR = Path(__file__).parent / "assets" / "farms"
ROOM_IMAGE = Path(__file__).parent / "room_edits" / "image.png"
BED_IMAGE = Path(__file__).parent / "room_edits" / "image copy.png"
SAD_LEWIS = Path(__file__).parent / "Characters" / "Lewis" / "sad_lewis.png"
SASSY_LEWIS = Path(__file__).parent / "Characters" / "Lewis" / "Sassy_lewis.png"
ROOM_FLOOR_BOUNDS = (32, 202, 555, 558)
BED_RENDER_SIZE = (100, 150)
BED_MOVE_STEP = 8
HAIR_FRONT_BY_STYLE: dict[int, int | None] = {
    0: None,
    1: 26,
    2: 26,
    3: 26,
    4: 26,
    5: 26,
    6: 26,
    7: 26,
    8: 26,
    9: 26,
    10: 26,
    11: None,
    12: None,
    13: None,
    14: 26,
    15: 26,
    16: 26,
    17: 26,
    18: 29,
    19: 26,
    20: 26,
    21: 26,
    22: 26,
    23: 26,
    24: 26,
    25: 26,
    26: 26,
    27: 26,
    28: 26,
    29: 26,
}
FARMS = [
    "Standard Farm",
    "Riverland Farm",
    "Forest Farm",
    "Hill-top Farm",
    "Wilderness Farm",
    "Four Corners Farm",
    "Beach Farm",
    "Meadowlands Farm",
]
FARM_SCENE_IMAGES = {
    "Standard Farm": Path(__file__).parent / "Farm_maps" / "Standard_farm.png",
    "Riverland Farm": Path(__file__).parent / "Farm_maps" / "Riverland_farm.png",
    "Forest Farm": Path(__file__).parent / "Farm_maps" / "Forest_farm.png",
    "Hill-top Farm": Path(__file__).parent / "Farm_maps" / "Hill-top_farm.png",
    "Wilderness Farm": Path(__file__).parent / "Farm_maps" / "Wilderness_farm.png",
    "Four Corners Farm": Path(__file__).parent / "Farm_maps" / "four_corners_farm.png",
    "Beach Farm": Path(__file__).parent / "Farm_maps" / "Beach_farm.png",
    "Meadowlands Farm": Path(__file__).parent / "Farm_maps" / "Meadowlands_farm.png",
}
FARM_FOLLOWUP_DIALOGUE = (
    ("It's a bit of a mess after your grandpa died.", SAD_LEWIS),
    ("It's not been looked after for quite some time.", SASSY_LEWIS),
    (
        "but i have faith in you that you will make it even better as it was.",
        HAPPY_LEWIS,
    ),
)
FARM_INFO = {
    "Standard Farm": (
        "10% bonus on farming. Holding animals here is easy. "
        "No monsters spawn at night here."
    ),
    "Riverland Farm": (
        "Fishing is 25% easier. Holding animals here is a bit difficult. "
        "If you reach level 10 on fishing, getting treasures is a bit easier."
    ),
    "Forest Farm": (
        "Possibility for random forages to be found. Finding wood here is easier. "
        "Less stone drops here."
    ),
    "Hill-top Farm": (
        "More stone appears, less wood. Artifacts have more chance to spawn here. "
        "No farming bonus."
    ),
    "Wilderness Farm": (
        "Monsters have a chance of spawning. Easier for forages to spawn. "
        "Stone drops less. Wood a bit more."
    ),
    "Four Corners Farm": (
        "It works exactly the same as Standard Farm but with 4 corners. "
        "10% bonus on farming. Holding animals here is easy. "
        "No monsters spawn here."
    ),
    "Beach Farm": (
        "25% better fishing. Farming speed and quality are 15% lower. "
        "Items may wash up from the ocean, from trash to rare artifacts. "
        "Trees and stones work normally here."
    ),
    "Meadowlands Farm": (
        "You get 2 chickens and a coop. Instead of receiving seeds, you receive hay. "
        "Stone and wood drops are normal."
    ),
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
EYE_PALETTES = json.loads(
    (Path(__file__).parent / "assets" / "eye_colors.json").read_text()
)
BASE_EYE_SHADES = [tuple(shade) + (255,) for shade in EYE_PALETTES[0]["shades"]]
HAIR_PALETTES = json.loads(
    (Path(__file__).parent / "assets" / "hair_colors.json").read_text()
)
BASE_HAIR_SHADES = [tuple(shade) for shade in HAIR_PALETTES[0]["shades"]]
SHIRT_IMAGE = Path(__file__).parent / "assets" / "shirt" / "shirt.png"
HAPPY_CLOSED_EYES_IMAGE = Path(__file__).parent / "assets" / "expressions" / "happy_closed_eyes.png"
HAPPY_SMILE_IMAGE = Path(__file__).parent / "assets" / "expressions" / "happy_smile.png"
SAD_EYES_IMAGE = Path(__file__).parent / "assets" / "expressions" / "sad_reference_eyes.png"
SAD_BROWS_IMAGE = Path(__file__).parent / "assets" / "expressions" / "sad_reference_brows.png"
SAD_LIPS_IMAGE = Path(__file__).parent / "assets" / "expressions" / "sad_reference_lips.png"
SAD_PURPLE_LIPS_IMAGE = Path(__file__).parent / "assets" / "expressions" / "sad_reference_purple_lips.png"
SAD_IRIS_COLOR_INDEX = {
    (12, 62, 33): 0,
    (35, 75, 37): 0,
    (30, 124, 70): 1,
    (81, 194, 133): 2,
}
SHIRT_PALETTES = json.loads(
    (Path(__file__).parent / "assets" / "shirt_colors.json").read_text()
)
BASE_SHIRT_SHADES = [tuple(shade) for shade in SHIRT_PALETTES[0]["shades"]]
COLOR_STAGES = {"eye_color", "hair_color", "shirt_color"}
COLOR_IMAGE_STAGES = {
    "eye_color": "eyes",
    "hair_color": "bangs",
    "shirt_color": "shirt",
}


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


def delete_progress(user_id: int) -> None:
    try:
        data = json.loads(PROGRESS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return
    if str(user_id) not in data:
        return
    del data[str(user_id)]
    temporary = PROGRESS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, separators=(",", ":")))
    os.replace(temporary, PROGRESS_FILE)


def delete_character_save(user_id: int) -> None:
    delete_progress(user_id)
    portrait_path = PROGRESS_FILE.parent / "portraits" / f"{user_id}.png"
    portrait_path.unlink(missing_ok=True)


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


def recolor_mark_layer(
    path: Path, skin_shade_map: dict[tuple[int, int, int], tuple[int, int, int]]
) -> Image.Image:
    layer = Image.open(path).convert("RGBA")
    pixels = layer.load()
    for y in range(layer.height):
        for x in range(layer.width):
            red, green, blue, alpha = pixels[x, y]
            replacement = skin_shade_map.get((red, green, blue))
            if replacement is not None:
                pixels[x, y] = (*replacement, alpha)
    return layer


def recolor_sad_brow_layer(
    path: Path, skin_shade_map: dict[tuple[int, int, int], tuple[int, int, int]]
) -> Image.Image:
    layer = Image.open(path).convert("RGBA")
    target_shades = {
        (239, 85, 33): skin_shade_map.get((255, 135, 110), (255, 135, 110)),
        (254, 116, 35): skin_shade_map.get((255, 170, 128), (255, 170, 128)),
    }
    pixels = layer.load()
    for y in range(layer.height):
        for x in range(layer.width):
            red, green, blue, alpha = pixels[x, y]
            replacement = target_shades.get((red, green, blue))
            if replacement is not None:
                pixels[x, y] = (*replacement, alpha)
    return layer


def tighten_sad_brow_spacing(layer: Image.Image) -> Image.Image:
    alpha = layer.getchannel("A")
    occupied_columns = [
        x
        for x in range(layer.width)
        if alpha.crop((x, 0, x + 1, layer.height)).getbbox() is not None
    ]
    gaps = list(zip(occupied_columns, occupied_columns[1:]))
    if not gaps:
        return layer
    left_column, right_column = max(gaps, key=lambda gap: gap[1] - gap[0])
    if right_column - left_column <= 1:
        return layer

    split = (left_column + right_column + 1) // 2
    adjusted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    adjusted.alpha_composite(layer.crop((0, 0, split, layer.height)), (8, 0))
    adjusted.alpha_composite(
        layer.crop((split, 0, layer.width, layer.height)), (split - 8, 0)
    )
    return adjusted


def compensate_for_dialogue_flip(layer: Image.Image) -> Image.Image:
    bounds = layer.getchannel("A").getbbox()
    if bounds is None:
        return layer
    mirrored = layer.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    horizontal_offset = bounds[0] - (layer.width - bounds[2])
    result = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    result.alpha_composite(mirrored, (horizontal_offset, 0))
    return result


def recolor_shirt_layer(
    path: Path,
    color_id: int,
    skin_shade_map: dict[tuple[int, int, int], tuple[int, int, int]],
) -> Image.Image:
    layer = Image.open(path).convert("RGBA")
    target_shades = SHIRT_PALETTES[color_id - 1]["shades"]
    shade_map = {
        source: tuple(max(0, min(255, channel)) for channel in target)
        for source, target in zip(BASE_SHIRT_SHADES, target_shades)
    }
    pixels = layer.load()
    for y in range(layer.height):
        for x in range(layer.width):
            red, green, blue, alpha = pixels[x, y]
            replacement = shade_map.get((red, green, blue)) or skin_shade_map.get(
                (red, green, blue)
            )
            if replacement is not None:
                pixels[x, y] = (*replacement, alpha)
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
    mark1_top_path: Path | None = None,
    mark1_bottom_path: Path | None = None,
    mark2_top_path: Path | None = None,
    mark2_bottom_path: Path | None = None,
    eye_overlay_path: Path | None = None,
    shirt_path: Path | None = None,
    shirt_color_id: int = 1,
    mouth_flip_vertical: bool = False,
    closed_eyes: bool = False,
    compensate_brow_dialogue_flip: bool = False,
) -> io.BytesIO:
    skin = Image.open(skin_path).convert("RGBA")
    eyes = Image.open(eye_path).convert("RGBA")
    eye_match = re.fullmatch(r"(\d+)\.eyeskin1", eye_path.stem, re.IGNORECASE)
    if eye_match is None:
        raise ValueError(f"Unexpected eye asset name: {eye_path.name}")
    skin_match = re.fullmatch(r"(\d+)\.skincolor\d+", skin_path.stem, re.IGNORECASE)
    if skin_match is None:
        raise ValueError(f"Unexpected skin asset name: {skin_path.name}")
    eye_reference = Image.open(BODY_DIR / f"{eye_match.group(1)}.png").convert("RGBA")
    skin_reference_dir = (
        MASCULINE_BODY_DIR
        if skin_path.parent == MASCULINE_SKIN_DIR
        else BODY_DIR
    )
    skin_reference = Image.open(
        skin_reference_dir / f"{skin_match.group(1)}.png"
    ).convert("RGBA")
    if skin.size != eyes.size or eyes.size != eye_reference.size or skin.size != skin_reference.size:
        raise ValueError("Skin, eye, and reference images must have the same dimensions.")

    skin_shade_map: dict[tuple[int, int, int], tuple[int, int, int]] = {}
    for source_pixel, target_pixel in zip(skin_reference.getdata(), skin.getdata()):
        if source_pixel[3] and target_pixel[3] and source_pixel[:3] != target_pixel[:3]:
            skin_shade_map[source_pixel[:3]] = target_pixel[:3]

    head_top_layers: list[Path] = []
    if hair_path is not None:
        with Image.open(hair_path) as hair_image:
            front_style = HAIR_FRONT_BY_STYLE.get(int(hair_path.stem), 26)
            if (
                front_style is not None
                and hair_image.convert("RGBA").getchannel("A").getbbox() is not None
            ):
                head_top_layers = [
                    BANGS_BOTTOM_DIR / f"{front_style}.png",
                    BANGS_TOP_DIR / f"{front_style}.png",
                ]
    back_layers = [
        (layer, True)
        for layer in (hair_path, *head_top_layers[:1], bangs_bottom_path)
        if layer is not None
    ] + [
        (layer, False)
        for layer in (mark1_bottom_path, mark2_bottom_path)
        if layer is not None
    ]
    if back_layers:
        body = skin.copy()
        body_pixels = body.load()
        for y in range(body.height):
            for x in range(body.width):
                red, green, blue, _ = body_pixels[x, y]
                if red >= 254 and green >= 254 and blue >= 254:
                    body_pixels[x, y] = (255, 255, 255, 0)
        background = Image.new("RGBA", skin.size, (255, 255, 255, 255))
        for layer_path, is_hair in back_layers:
            layer = (
                recolor_hair_layer(layer_path, hair_color_id)
                if is_hair
                else recolor_mark_layer(layer_path, skin_shade_map)
            )
            layer = layer.resize(skin.size, Image.Resampling.NEAREST)
            background.alpha_composite(layer)
        background.alpha_composite(body)
        skin = background
    target_shades = EYE_PALETTES[color_id - 1]["shades"]
    shade_map = {
        source: tuple(max(0, min(255, channel)) for channel in target) + (255,)
        for source, target in zip(BASE_EYE_SHADES, target_shades)
    }
    skin_pixels = skin.load()
    eye_pixels = eyes.load()
    reference_pixels = eye_reference.load()
    sad_eye_overlay = None
    if eye_overlay_path is None:
        for y in range(85, min(146, skin.height)):
            for x in range(skin.width):
                eye_pixel = eye_pixels[x, y]
                if eye_pixel != reference_pixels[x, y]:
                    if not closed_eyes:
                        skin_pixels[x, y] = shade_map.get(eye_pixel, eye_pixel)
    if eye_overlay_path is not None:
        with Image.open(eye_overlay_path) as source:
            eye_overlay = source.convert("RGBA")
        if eye_overlay.size != skin.size:
            raise ValueError("Sad eye overlay must match the profile size.")
        eye_overlay_pixels = eye_overlay.load()
        for x in range(eye_overlay.width):
            for y in range(eye_overlay.height):
                red, green, blue, alpha = eye_overlay_pixels[x, y]
                source_color = (red, green, blue)
                skin_color = skin_shade_map.get(source_color)
                shade_index = SAD_IRIS_COLOR_INDEX.get(source_color)
                if skin_color is not None:
                    eye_overlay_pixels[x, y] = (*skin_color, alpha)
                elif shade_index is not None:
                    target_shade = target_shades[shade_index]
                    eye_overlay_pixels[x, y] = (*target_shade, alpha)
        sad_eye_overlay = eye_overlay
    if closed_eyes:
        with Image.open(HAPPY_CLOSED_EYES_IMAGE) as source:
            closed_eye_layer = source.convert("RGBA")
        if closed_eye_layer.size != skin.size:
            raise ValueError("Happy closed-eye overlay must match the profile size.")
        skin.alpha_composite(closed_eye_layer)

    if shirt_path is not None:
        shirt = recolor_shirt_layer(shirt_path, shirt_color_id, skin_shade_map)
        shirt = shirt.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(shirt)
    if brow_path is not None and eye_overlay_path is None:
        brows = Image.open(brow_path).convert("RGBA")
        brows = brows.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(brows)
    if sad_eye_overlay is not None:
        skin.alpha_composite(sad_eye_overlay)
        if brow_path is not None:
            brows = recolor_sad_brow_layer(brow_path, skin_shade_map)
            brows = brows.resize(skin.size, Image.Resampling.NEAREST)
            brows = tighten_sad_brow_spacing(brows)
            if compensate_brow_dialogue_flip:
                brows = compensate_for_dialogue_flip(brows)
            skin.alpha_composite(brows)
    if nose_path is not None:
        nose = Image.open(nose_path).convert("RGBA")
        nose = nose.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(nose)
    if mouth_path is not None:
        mouth = Image.open(mouth_path).convert("RGBA")
        if mouth_flip_vertical:
            mouth_bounds = mouth.getchannel("A").getbbox()
            if mouth_bounds is not None:
                flipped_mouth = Image.new("RGBA", mouth.size, (0, 0, 0, 0))
                flipped_mouth.alpha_composite(
                    mouth.crop(mouth_bounds).transpose(Image.Transpose.FLIP_TOP_BOTTOM),
                    mouth_bounds[:2],
                )
                mouth = flipped_mouth
        mouth = mouth.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(mouth)
    for mark_path in (mark1_top_path, mark2_top_path):
        if mark_path is not None:
            mark = recolor_mark_layer(mark_path, skin_shade_map)
            mark = mark.resize(skin.size, Image.Resampling.NEAREST)
            skin.alpha_composite(mark)
    if head_top_layers:
        head_top = recolor_hair_layer(head_top_layers[1], hair_color_id)
        head_top = head_top.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(head_top)
    if bangs_top_path is not None:
        bangs_top = recolor_hair_layer(bangs_top_path, hair_color_id)
        bangs_top = bangs_top.resize(skin.size, Image.Resampling.NEAREST)
        skin.alpha_composite(bangs_top)

    output = io.BytesIO()
    skin.save(output, format="PNG")
    output.seek(0)
    return output


def render_farm_picker() -> io.BytesIO:
    cell_width, cell_height = 340, 220
    outer = 24
    gap_x, gap_y = 18, 14
    header_height = 82
    width = outer * 2 + cell_width * 2 + gap_x
    height = outer * 2 + header_height + cell_height * 4 + gap_y * 3
    sheet = Image.new("RGBA", (width, height), (51, 112, 150, 255))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, int(height * 0.76), width, height), fill=(79, 138, 77, 255))
    draw.rectangle((0, int(height * 0.76), width, int(height * 0.76) + 10), fill=(112, 174, 92, 255))
    draw.rounded_rectangle(
        (10, 10, width - 10, height - 10),
        radius=14,
        fill=(104, 68, 43, 255),
        outline=(236, 170, 78, 255),
        width=6,
    )
    draw.rounded_rectangle(
        (outer - 8, outer - 8, width - outer + 8, height - outer + 8),
        radius=10,
        fill=(246, 214, 167, 255),
        outline=(255, 237, 200, 255),
        width=4,
    )
    title_font = ImageFont.load_default(size=34)
    title = "Choose Your Farm"
    title_width = draw.textlength(title, font=title_font)
    draw.text(
        ((width - title_width) / 2, outer + 8),
        title,
        font=title_font,
        fill=(102, 57, 45, 255),
        stroke_width=1,
        stroke_fill=(255, 237, 200, 255),
    )
    label_font = ImageFont.load_default(size=20)
    for index, name in enumerate(FARMS):
        farm = Image.open(FARMS_DIR / f"{index + 1}.png").convert("RGBA")
        column, row = divmod(index, 4)
        left = outer + column * (cell_width + gap_x)
        top = outer + header_height + row * (cell_height + gap_y)
        draw.rounded_rectangle(
            (left, top, left + cell_width, top + cell_height),
            radius=8,
            fill=(183, 120, 70, 255),
            outline=(128, 77, 48, 255),
            width=4,
        )
        draw.rectangle(
            (left + 7, top + 7, left + cell_width - 7, top + cell_height - 7),
            fill=(248, 209, 151, 255),
            outline=(255, 235, 191, 255),
            width=2,
        )
        scale = 3
        farm = farm.resize((farm.width * scale, farm.height * scale), Image.Resampling.NEAREST)
        sheet.alpha_composite(
            farm,
            (left + (cell_width - farm.width) // 2, top + 5),
        )
        text_width = draw.textlength(name, font=label_font)
        draw.text(
            (left + (cell_width - text_width) / 2, top + 187),
            name,
            font=label_font,
            fill=(90, 53, 42, 255),
        )
    output = io.BytesIO()
    sheet.save(output, format="PNG")
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


def load_body_images(gender: str = "feminine") -> list[Path]:
    if gender == "masculine":
        body_dir = MASCULINE_BODY_DIR
    elif gender == "feminine":
        body_dir = BODY_DIR
    else:
        raise ValueError(f"Unsupported character body type: {gender}")
    if not body_dir.is_dir():
        return []
    return sorted(
        (p for p in body_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES),
        key=natural_key,
    )


def load_skin_images(face_name: str, gender: str = "feminine") -> list[Path]:
    if gender == "masculine":
        skin_dir = MASCULINE_SKIN_DIR
    elif gender == "feminine":
        skin_dir = SKIN_DIR
    else:
        raise ValueError(f"Unsupported character body type: {gender}")
    if not skin_dir.is_dir():
        return []
    return sorted(
        (
            p
            for p in skin_dir.iterdir()
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


def load_mark_images() -> list[Path]:
    if not MARKS_TOP_DIR.is_dir() or not MARKS_BOTTOM_DIR.is_dir():
        return []
    return sorted(
        (
            top_path
            for top_path in MARKS_TOP_DIR.iterdir()
            if top_path.suffix.lower() in IMAGE_SUFFIXES
            and (MARKS_BOTTOM_DIR / top_path.name).is_file()
        ),
        key=natural_key,
    )


class BodyView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        images: list[Path],
        character_name: str = "",
        gender: str = "feminine",
    ) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.character_name = character_name
        self.gender = gender
        self.images = images
        self.index = 0
        self.step_images: dict[str, list[Path]] = {"shape": images}
        self.step_indices: dict[str, int] = {"shape": 0}
        self.message: discord.Message | None = None
        self.colors: "ColorView | None" = None
        self.stage = "shape"
        self.test_mode = False
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
        self.selected_mark1_top_image: Path | None = None
        self.selected_mark1_bottom_image: Path | None = None
        self.selected_mark2_top_image: Path | None = None
        self.selected_mark2_bottom_image: Path | None = None
        self.hair_color_id = 1
        self.shirt_color_id = 1
        self.eyes_button: CategoryButton | None = None
        self.brows_button: CategoryButton | None = None
        self.nose_button: CategoryButton | None = None
        self.mouth_button: CategoryButton | None = None
        self.hair_button: CategoryButton | None = None
        self.bangs_button: CategoryButton | None = None
        self.mark1_button: CategoryButton | None = None
        self.mark2_button: CategoryButton | None = None
        self.shirt_button: CategoryButton | None = None
        self.shape_button = CategoryButton("Shape", row=1, stage="shape", selected=True)
        self.done_button = DoneButton("Shape Done", row=1)
        self.add_item(self.shape_button)
        self.add_item(self.done_button)

    @classmethod
    def restore(cls, owner_id: int, saved: dict) -> "BodyView | None":
        gender = saved.get("gender", "feminine")
        shape_images = load_body_images(gender)
        if not shape_images:
            return None
        view = cls(owner_id, shape_images, gender=gender)
        view.character_name = saved.get("character_name", "")
        view.selected_face = saved.get("selected_face")
        view.eye_color_id = int(saved.get("eye_color_id", 1))
        view.hair_color_id = int(saved.get("hair_color_id", 1))
        view.shirt_color_id = int(saved.get("shirt_color_id", 1))
        view.step_indices.update(
            {key: max(0, int(value)) for key, value in saved.get("step_indices", {}).items()}
        )

        loaders = {
            "skin": lambda: load_skin_images(
                view.selected_face or "", view.gender
            ),
            "eyes": load_eye_images,
            "brows": load_brow_images,
            "nose": load_nose_images,
            "mouth": load_mouth_images,
            "hair": load_hair_images,
            "bangs": load_bang_images,
            "mark1": load_mark_images,
            "mark2": load_mark_images,
            "shirt": lambda: [SHIRT_IMAGE] if SHIRT_IMAGE.is_file() else [],
        }
        for step in saved.get("steps", []):
            if step in loaders:
                images = loaders[step]()
                if images:
                    view.step_images[step] = images

        saved_stage = saved.get("stage", "shape")
        image_stage = COLOR_IMAGE_STAGES.get(saved_stage, saved_stage)
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

        for step in ("mark1", "mark2"):
            marks = view.step_images.get(step)
            if marks:
                marks_index = min(view.step_indices.get(step, 0), len(marks) - 1)
                top = marks[marks_index]
                bottom = MARKS_BOTTOM_DIR / top.name
                setattr(view, f"selected_{step}_top_image", top)
                setattr(view, f"selected_{step}_bottom_image", bottom)

        for step, label in (
            ("eyes", "Eyes"),
            ("brows", "Brows"),
            ("nose", "Nose"),
            ("mouth", "Mouth"),
            ("hair", "Hair"),
            ("bangs", "Bangs"),
            ("mark1", "Mark1"),
            ("mark2", "Mark2"),
            ("shirt", "Shirt"),
        ):
            if step in view.step_images:
                button = CategoryButton(label, row=1, stage=step)
                setattr(view, f"{step}_button", button)
                view.add_step_button(button)
        view.update_stage_buttons()
        return view

    def save_progress(self) -> None:
        if self.stage not in COLOR_STAGES:
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
        elif self.stage in {"mark1", "mark2"}:
            setattr(self, f"selected_{self.stage}_top_image", self.images[self.index])
            setattr(
                self,
                f"selected_{self.stage}_bottom_image",
                MARKS_BOTTOM_DIR / self.images[self.index].name,
            )

        if self.test_mode:
            return
        saved_progress = read_progress(self.owner_id) or {}
        write_progress(
            self.owner_id,
            {
                "stage": self.stage,
                "character_name": self.character_name or saved_progress.get("character_name", ""),
                "farm_name": saved_progress.get("farm_name", ""),
                "coins": int(saved_progress.get("coins", 0)),
                "daily_earnings": int(saved_progress.get("daily_earnings", 0)),
                "day": int(saved_progress.get("day", 1)),
                "season": saved_progress.get("season", "Spring"),
                "year": int(saved_progress.get("year", 1)),
                "selected_face": self.selected_face,
                "gender": self.gender,
                "step_indices": self.step_indices,
                "steps": list(self.step_images),
                "eye_color_id": self.eye_color_id,
                "hair_color_id": self.hair_color_id,
                "shirt_color_id": self.shirt_color_id,
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
            "mark1": "Mark1",
            "mark2": "Mark2",
            "shirt": "Shirt",
            "shirt_color": "Shirt Color",
        }[self.stage]
        if self.stage == "eye_color":
            label_index = self.eye_color_id
        elif self.stage == "shirt_color":
            label_index = self.shirt_color_id
        elif self.stage == "hair_color":
            label_index = self.hair_color_id
        elif self.stage == "brows":
            label_index = self.index
        elif self.stage in {"nose", "mouth", "hair", "bangs", "mark1", "mark2"}:
            label_index = self.index
        else:
            label_index = self.index + 1
        self.face.label = f"{kind} {label_index}"
        if self.stage in {"eyes", "eye_color", "brows", "nose", "mouth", "hair", "bangs", "hair_color", "mark1", "mark2", "shirt", "shirt_color"} and self.selected_skin_image:
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
            mark1_top_path = path if self.stage == "mark1" else self.selected_mark1_top_image
            mark1_bottom_path = (
                MARKS_BOTTOM_DIR / path.name
                if self.stage == "mark1"
                else self.selected_mark1_bottom_image
            )
            mark2_top_path = path if self.stage == "mark2" else self.selected_mark2_top_image
            mark2_bottom_path = (
                MARKS_BOTTOM_DIR / path.name
                if self.stage == "mark2"
                else self.selected_mark2_bottom_image
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
                mark1_top_path,
                mark1_bottom_path,
                mark2_top_path,
                mark2_bottom_path,
                SHIRT_IMAGE if "shirt" in self.step_images else None,
                self.shirt_color_id,
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
            "mark1": self.mark1_button,
            "mark2": self.mark2_button,
            "shirt": self.shirt_button,
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
            "mark1": "Mark1 Done",
            "mark2": "Mark2 Done",
            "shirt": "Shirt Done",
            "shirt_color": "Shirt Color Done",
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
        image_stage = COLOR_IMAGE_STAGES.get(stage, stage)
        images = self.step_images.get(image_stage, [])
        if not images:
            await interaction.response.send_message(
                f"{stage.replace('_', ' ').title()} is not available yet.",
                ephemeral=True,
            )
            return

        if self.stage not in COLOR_STAGES:
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
        elif self.stage == "mark1":
            self.selected_mark1_top_image = self.images[self.index]
            self.selected_mark1_bottom_image = MARKS_BOTTOM_DIR / self.images[self.index].name
        elif self.stage == "mark2":
            self.selected_mark2_top_image = self.images[self.index]
            self.selected_mark2_bottom_image = MARKS_BOTTOM_DIR / self.images[self.index].name
        elif self.stage == "hair_color":
            self.selected_bangs_top_image = self.step_images["bangs"][
                self.step_indices.get("bangs", 0)
            ]
            self.selected_bangs_bottom_image = (
                BANGS_BOTTOM_DIR / self.selected_bangs_top_image.name
            )
        elif self.stage in {"mark1", "mark2"}:
            mark_path = self.images[self.index]
            setattr(self, f"selected_{self.stage}_top_image", mark_path)
            setattr(
                self,
                f"selected_{self.stage}_bottom_image",
                MARKS_BOTTOM_DIR / mark_path.name,
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
        elif stage in {"mark1", "mark2"}:
            mark_path = self.images[self.index]
            setattr(self, f"selected_{stage}_top_image", mark_path)
            setattr(
                self,
                f"selected_{stage}_bottom_image",
                MARKS_BOTTOM_DIR / mark_path.name,
            )
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
            await self.finish_hair_color(interaction)
        elif self.stage == "mark1":
            await self.finish_mark1(interaction)
        elif self.stage == "mark2":
            await self.finish_mark2(interaction)
        elif self.stage == "shirt":
            await self.select_stage(interaction, "shirt_color")
        elif self.stage == "shirt_color":
            await self.finish_shirt_color(interaction)

    async def finish_shape(self, interaction: discord.Interaction) -> None:
        face_name = self.images[self.index].stem
        shape_changed = self.selected_face != face_name
        self.selected_face = face_name
        skin_images = load_skin_images(face_name, self.gender)
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
            self.step_indices.setdefault("bangs", 0)
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

    async def finish_hair_color(self, interaction: discord.Interaction) -> None:
        mark_images = load_mark_images()
        if not mark_images:
            await interaction.response.send_message(
                "No Mark1/Mark2 images found in assets/marks.", ephemeral=True
            )
            return

        self.step_images["mark1"] = mark_images
        self.step_images["mark2"] = mark_images
        self.step_indices.setdefault("mark1", 0)
        self.step_indices.setdefault("mark2", 0)
        if self.mark1_button is None:
            self.mark1_button = CategoryButton("Mark1", row=1, stage="mark1")
            self.add_step_button(self.mark1_button)
        if self.mark2_button is None:
            self.mark2_button = CategoryButton("Mark2", row=1, stage="mark2")
            self.add_step_button(self.mark2_button)
        await self.select_stage(interaction, "mark1")

    async def finish_mark1(self, interaction: discord.Interaction) -> None:
        self.selected_mark1_top_image = self.images[self.index]
        self.selected_mark1_bottom_image = MARKS_BOTTOM_DIR / self.images[self.index].name
        self.step_indices["mark1"] = self.index
        await self.select_stage(interaction, "mark2")

    async def finish_mark2(self, interaction: discord.Interaction) -> None:
        self.selected_mark2_top_image = self.images[self.index]
        self.selected_mark2_bottom_image = MARKS_BOTTOM_DIR / self.images[self.index].name
        self.step_indices["mark2"] = self.index
        if not SHIRT_IMAGE.is_file():
            await interaction.response.send_message(
                "No shirt image found in assets/shirt.", ephemeral=True
            )
            return

        self.step_images["shirt"] = [SHIRT_IMAGE]
        self.step_indices["shirt"] = 0
        if self.shirt_button is None:
            self.shirt_button = CategoryButton("Shirt", row=1, stage="shirt")
            self.add_step_button(self.shirt_button)
        if self.colors is not None:
            self.colors.add_shirt_color_button()
        await self.select_stage(interaction, "shirt_color")
        await interaction.followup.send(
            "Don't worry, you are able to get more clothes later.", ephemeral=True
        )

    def save_portrait(self) -> None:
        portrait = self.current().fp.getvalue()
        path = PROGRESS_FILE.parent / "portraits" / f"{self.owner_id}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(portrait)

    async def finish_shirt_color(self, interaction: discord.Interaction) -> None:
        self.save_progress()
        await interaction.response.edit_message(view=FinishView(self))
        if self.colors is not None and self.colors.message is not None:
            try:
                await self.colors.message.delete()
            except discord.HTTPException:
                pass
            self.colors.message = None

    async def go_back(self, interaction: discord.Interaction) -> None:
        self.update_stage_buttons()
        await interaction.response.edit_message(view=self)
        if self.colors is not None:
            self.colors.update_stage_buttons(self.stage, self.step_images)
            self.colors.message = await interaction.message.reply(
                "Colors", view=self.colors
            )

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.stage == "eye_color":
            self.eye_color_id = (self.eye_color_id - 2) % len(EYE_PALETTES) + 1
        elif self.stage == "hair_color":
            self.hair_color_id = (self.hair_color_id - 2) % len(HAIR_PALETTES) + 1
        elif self.stage == "shirt_color":
            self.shirt_color_id = (self.shirt_color_id - 2) % len(SHIRT_PALETTES) + 1
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
        elif self.stage == "shirt_color":
            self.shirt_color_id = self.shirt_color_id % len(SHIRT_PALETTES) + 1
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
        if self.view.body_view.test_mode:
            await interaction.response.send_message(
                "Test mode: nothing is saved.", ephemeral=True
            )
            return
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
        self.shirt_color_button: ColorButton | None = None
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

    def add_shirt_color_button(self) -> None:
        if self.shirt_color_button is not None:
            return
        self.shirt_color_button = ColorButton("Shirt Color", "shirt_color", row=0)
        self.shirt_color_button.disabled = True
        self.add_before_save(self.shirt_color_button)

    def update_stage_buttons(
        self, selected_stage: str, available_images: dict[str, list[Path]]
    ) -> None:
        buttons = {
            "skin": self.skin_button,
            "eye_color": self.eye_color_button,
            "hair_color": self.hair_color_button,
            "shirt_color": self.shirt_color_button,
        }
        for stage, button in buttons.items():
            if button is None:
                continue
            image_stage = COLOR_IMAGE_STAGES.get(stage, stage)
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


class FinishView(discord.ui.View):
    def __init__(self, body_view: BodyView) -> None:
        super().__init__(timeout=600)
        self.body_view = body_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.body_view.owner_id:
            await interaction.response.send_message(
                "This is not your farm.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="All Done", style=discord.ButtonStyle.success)
    async def all_done(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(
            content="Are you sure you are all done?",
            view=ConfirmDoneView(self.body_view),
        )
        self.stop()

    @discord.ui.button(label="Go Back", style=discord.ButtonStyle.secondary)
    async def go_back(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.body_view.go_back(interaction)
        self.stop()


class ConfirmDoneView(discord.ui.View):
    def __init__(self, body_view: BodyView) -> None:
        super().__init__(timeout=600)
        self.body_view = body_view

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.body_view.owner_id:
            await interaction.response.send_message(
                "This is not your farm.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if self.body_view.test_mode:
            await interaction.response.edit_message(
                content="Test finished. Your saved portrait was not changed.",
                attachments=[],
                view=None,
            )
            self.stop()
            return
        self.body_view.save_progress()
        self.body_view.save_portrait()
        write_progress(
            self.body_view.owner_id,
            {**read_progress(self.body_view.owner_id), "completed": True},
        )
        await interaction.response.edit_message(
            content="You look amazing!", attachments=[], view=None
        )
        self.stop()
        await asyncio.sleep(3)
        await interaction.message.edit(content="Now it's time to choose your farm!")
        await show_farm_picker(interaction.message, self.body_view.owner_id)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.edit_message(
            content=None, view=FinishView(self.body_view)
        )
        self.stop()


class FarmButton(discord.ui.Button):
    def __init__(self, name: str, row: int) -> None:
        super().__init__(label=name, style=discord.ButtonStyle.secondary, row=row)
        self.farm_name = name

    async def callback(self, interaction: discord.Interaction) -> None:
        info = FARM_INFO.get(self.farm_name)
        if info is None:
            await interaction.response.send_message(
                f"You picked the {self.farm_name}.", ephemeral=True
            )
            return
        picker = interaction.message
        await interaction.response.edit_message(view=None)
        await picker.reply(
            f"{info}\n\nAre you sure you want this farm?",
            view=ConfirmFarmView(interaction.user.id, self.farm_name, picker),
        )
        if self.farm_name == "Four Corners Farm":
            await interaction.followup.send(
                "I will try to add multiplayer features. try to add it eventually if its an option.",
                ephemeral=True,
            )


def render_profile_portrait(owner_id: int, expression: str = "normal") -> Image.Image:
    portrait_path = PROGRESS_FILE.parent / "portraits" / f"{owner_id}.png"
    if expression == "normal":
        with Image.open(portrait_path) as source:
            return source.convert("RGBA")

    saved = read_progress(owner_id) or {}
    body = BodyView.restore(owner_id, saved)
    if (
        body is None
        or body.selected_skin_image is None
        or body.selected_eye_image is None
    ):
        raise FileNotFoundError("The saved profile cannot be rendered with this expression.")

    eye_path = body.selected_eye_image
    mouth_path = body.selected_mouth_image
    eye_overlay_path = None
    if expression == "happy":
        mouth_path = HAPPY_SMILE_IMAGE
    elif expression == "sad":
        eye_overlay_path = SAD_EYES_IMAGE
        if body.selected_mouth_image is None:
            mouth_path = SAD_PURPLE_LIPS_IMAGE
        else:
            with Image.open(body.selected_mouth_image) as selected_mouth:
                mouth_path = (
                    SAD_LIPS_IMAGE
                    if selected_mouth.getchannel("A").getbbox() is not None
                    else SAD_PURPLE_LIPS_IMAGE
                )

    brow_path = body.selected_brow_image
    if expression == "happy":
        brow_path = None
    elif expression == "sad":
        brow_path = SAD_BROWS_IMAGE
    portrait_file = render_eye_preview(
        body.selected_skin_image,
        eye_path,
        body.eye_color_id,
        brow_path=brow_path,
        nose_path=body.selected_nose_image,
        mouth_path=mouth_path,
        hair_path=body.selected_hair_image,
        bangs_top_path=body.selected_bangs_top_image,
        bangs_bottom_path=body.selected_bangs_bottom_image,
        hair_color_id=body.hair_color_id,
        mark1_top_path=body.selected_mark1_top_image,
        mark1_bottom_path=body.selected_mark1_bottom_image,
        mark2_top_path=body.selected_mark2_top_image,
        mark2_bottom_path=body.selected_mark2_bottom_image,
        eye_overlay_path=eye_overlay_path,
        shirt_path=SHIRT_IMAGE if "shirt" in body.step_images else None,
        shirt_color_id=body.shirt_color_id,
        closed_eyes=expression == "happy",
        compensate_brow_dialogue_flip=expression == "sad",
    )
    with Image.open(portrait_file) as source:
        return source.convert("RGBA")


class ArrivalContinueView(discord.ui.View):
    def __init__(self, owner_id: int, stage: str = "arrival") -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.stage = stage

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This arrival scene belongs to someone else.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_arrival(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        saved = read_progress(self.owner_id) or {}
        if saved.get("pending_farm") is None:
            await interaction.response.edit_message(
                content="Your farm choice is no longer available.", view=None
            )
            self.stop()
            return

        if self.stage == "arrival":
            await interaction.response.edit_message(
                content=None,
                attachments=[
                    discord.File(
                        dialogue_scene(JOURNEY_QUESTION, NORMAL_LEWIS),
                        filename="scene.png",
                    )
                ],
                view=ArrivalContinueView(self.owner_id, stage="question"),
            )
        else:
            portrait_path = PROGRESS_FILE.parent / "portraits" / f"{self.owner_id}.png"
            if not portrait_path.is_file():
                await interaction.response.edit_message(
                    content="Your saved profile picture is missing.", view=None
                )
                self.stop()
                return
            await interaction.response.edit_message(
                content=None,
                attachments=[
                    discord.File(
                        dialogue_scene(
                            "\n".join(JOURNEY_CHOICES),
                            player_portrait=portrait_path,
                            scale=3,
                        ),
                        filename="scene.png",
                    )
                ],
                view=JourneyResponseView(self.owner_id),
            )
        self.stop()


class JourneyResponseView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This arrival scene belongs to someone else.", ephemeral=True
            )
            return False
        return True

    async def choose_response(
        self,
        interaction: discord.Interaction,
        response: str,
        expression: str,
        lewis_reply: str,
        lewis_expression: str,
    ) -> None:
        saved = read_progress(self.owner_id) or {}
        if saved.get("pending_farm") is None:
            await interaction.response.edit_message(
                content="Your farm choice is no longer available.", view=None
            )
            self.stop()
            return
        portrait = render_profile_portrait(self.owner_id, expression)
        scene = dialogue_scene(response, player_portrait=portrait)
        scene = dialogue_scene(response, player_portrait=portrait)
        await interaction.response.edit_message(
            content=None,
            attachments=[discord.File(scene, filename="scene.png")],
            view=JourneyPlayerResponseView(
                self.owner_id, lewis_reply, lewis_expression
            ),
        )
        self.stop()

    @discord.ui.button(label="1. It went alright", style=discord.ButtonStyle.secondary, row=0)
    async def alright(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.choose_response(
            interaction,
            "It went alright",
            "normal",
            "It could be worse, should we get started?",
            "normal",
        )

    @discord.ui.button(
        label="2. it went amazing, i cant wait to get started.",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def amazing(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.choose_response(
            interaction,
            "it went amazing, i cant wait to get started.",
            "happy",
            "I'm glad to hear you're so eager to start.",
            "happy",
        )

    @discord.ui.button(label="3. it went horrible.", style=discord.ButtonStyle.secondary, row=2)
    async def horrible(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.choose_response(
            interaction,
            "it went horrible.",
            "sad",
            "Oh, I'm sorry to hear. We should get started.",
            "sad",
        )


class JourneyPlayerResponseView(discord.ui.View):
    def __init__(self, owner_id: int, reply: str, expression: str) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.reply = reply
        self.expression = expression

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This arrival scene belongs to someone else.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_player_response(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        lewis_image = {
            "normal": NORMAL_LEWIS,
            "happy": HAPPY_LEWIS,
            "sad": SAD_LEWIS,
        }[self.expression]
        scene = dialogue_scene(self.reply, lewis_image=lewis_image)
        await interaction.response.edit_message(
            content=None,
            attachments=[discord.File(scene, filename="scene.png")],
            view=JourneyLewisReplyView(
                self.owner_id, self.reply, self.expression
            ),
        )
        self.stop()


class JourneyLewisReplyView(discord.ui.View):
    def __init__(self, owner_id: int, reply: str, expression: str) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.reply = reply
        self.expression = expression

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This arrival scene belongs to someone else.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_reply(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        saved = read_progress(self.owner_id) or {}
        pending_farm = saved.pop("pending_farm", None)
        if pending_farm is None:
            await interaction.response.edit_message(
                content="Your farm choice is no longer available.", view=None
            )
            self.stop()
            return

        farm_image_path = FARM_SCENE_IMAGES.get(pending_farm)
        if farm_image_path is None or not farm_image_path.is_file():
            await interaction.response.edit_message(
                content="The image for your selected farm is unavailable.", view=None
            )
            self.stop()
            return

        lewis_image = {
            "normal": NORMAL_LEWIS,
            "happy": HAPPY_LEWIS,
            "sad": SAD_LEWIS,
        }[self.expression]
        dialogue_frame = dialogue_scene(self.reply, lewis_image=lewis_image)
        with Image.open(dialogue_frame) as source:
            dialogue_image = source.convert("RGB")
        with Image.open(farm_image_path) as source:
            farm_image = source.convert("RGB")
        saved["farm"] = pending_farm
        saved["phase"] = "arrived"
        write_progress(self.owner_id, saved)
        await interaction.response.defer()
        await play_farm_reveal(interaction.message, dialogue_image, farm_image)
        await asyncio.sleep(1)
        announcement = dialogue_scene(
            "This is your new farm!",
            lewis_image=HAPPY_LEWIS,
            background_image=farm_image,
        )
        await interaction.message.edit(
            content=None,
            attachments=[discord.File(announcement, filename="scene.png")],
            view=FarmDialogueContinueView(self.owner_id, pending_farm),
        )
        self.stop()


class FarmDialogueContinueView(discord.ui.View):
    def __init__(self, owner_id: int, farm_name: str, step: int = 0) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.farm_name = farm_name
        self.step = step

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This arrival scene belongs to someone else.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_dialogue(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        farm_image_path = FARM_SCENE_IMAGES.get(self.farm_name)
        if farm_image_path is None or not farm_image_path.is_file():
            await interaction.response.edit_message(
                content="The image for your selected farm is unavailable.", view=None
            )
            self.stop()
            return

        text, lewis_image = FARM_FOLLOWUP_DIALOGUE[self.step]
        with Image.open(farm_image_path) as source:
            farm_image = source.convert("RGB")
        dialogue = dialogue_scene(
            text, lewis_image=lewis_image, background_image=farm_image
        )
        next_step = self.step + 1
        next_view = (
            FarmDialogueContinueView(self.owner_id, self.farm_name, next_step)
            if next_step < len(FARM_FOLLOWUP_DIALOGUE)
            else None
        )
        await interaction.response.edit_message(
            content=None,
            attachments=[discord.File(dialogue, filename="scene.png")],
            view=next_view,
        )
        self.stop()


class ConfirmFarmView(discord.ui.View):
    def __init__(
        self, owner_id: int, farm_name: str, picker: discord.Message
    ) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.farm_name = farm_name
        self.picker = picker

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This is not your farm.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        saved = read_progress(self.owner_id) or {}
        saved.pop("farm", None)
        write_progress(
            self.owner_id,
            {**saved, "pending_farm": self.farm_name, "phase": "arrival"},
        )
        await interaction.response.defer()
        await interaction.message.delete()
        self.stop()
        await play_arrival(
            self.picker,
            Image.open(render_farm_picker()),
            completion_view=ArrivalContinueView(self.owner_id),
        )

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.picker.edit(view=FarmView(self.owner_id))
        await interaction.message.delete()
        self.stop()


class FarmView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        for row in range(4):
            self.add_item(FarmButton(FARMS[row], row))
            self.add_item(FarmButton(FARMS[row + 4], row))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This is not your farm.", ephemeral=True
            )
            return False
        return True


class BedMoveButton(discord.ui.Button):
    def __init__(self, label: str, dx: int, dy: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=0)
        self.dx = dx
        self.dy = dy

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RoomTestView = self.view
        view.move(self.dx, self.dy)
        preview = view.render()
        await interaction.response.edit_message(
            attachments=[discord.File(preview, filename="room_test.png")],
            view=view,
        )


class RoomTestView(discord.ui.View):
    def __init__(self, owner_id: int, room_path: Path, bed_path: Path) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.room_path = room_path
        with Image.open(bed_path) as source:
            self.bed = source.convert("RGBA")
        self.bed = self.bed.resize(
            BED_RENDER_SIZE,
            Image.Resampling.NEAREST,
        )
        left, top, right, bottom = ROOM_FLOOR_BOUNDS
        opaque_left, opaque_top, opaque_right, opaque_bottom = (
            self.bed.getchannel("A").getbbox()
        )
        self.min_x = left - opaque_left
        self.min_y = top - opaque_top
        self.max_x = right - opaque_right
        self.max_y = bottom - opaque_bottom
        self.x = max(self.min_x, min(self.max_x, (left + right - self.bed.width) // 2))
        self.y = max(self.min_y, min(self.max_y, (top + bottom - self.bed.height) // 2))
        self.add_item(BedMoveButton("⬅️", -BED_MOVE_STEP, 0))
        self.add_item(BedMoveButton("⬆️", 0, -BED_MOVE_STEP))
        self.add_item(BedMoveButton("⬇️", 0, BED_MOVE_STEP))
        self.add_item(BedMoveButton("➡️", BED_MOVE_STEP, 0))

    def move(self, dx: int, dy: int) -> None:
        self.x = max(self.min_x, min(self.max_x, self.x + dx))
        self.y = max(self.min_y, min(self.max_y, self.y + dy))

    def render(self) -> io.BytesIO:
        with Image.open(self.room_path) as source:
            room = source.convert("RGBA")
        room.alpha_composite(self.bed, (self.x, self.y))
        output = io.BytesIO()
        room.save(output, format="PNG")
        output.seek(0)
        return output

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This is not your room.", ephemeral=True
            )
            return False
        return True


async def show_farm_picker(message: discord.Message, owner_id: int) -> None:
    await asyncio.sleep(3)
    try:
        picker = render_farm_picker()
    except OSError:
        await message.edit(content="Farm images are missing in assets/farms.")
        return
    await message.edit(
        attachments=[discord.File(picker, filename="farms.png")],
        view=FarmView(owner_id),
    )


class ResumeView(discord.ui.View):
    def __init__(self, owner_id: int, saved_progress: dict) -> None:
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.saved_progress = saved_progress

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This question is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.success)
    async def continue_farm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not self.saved_progress.get("character_name"):
            await interaction.response.send_modal(
                CharacterNameModal(
                    self.owner_id,
                    interaction.message,
                    resume_progress=self.saved_progress,
                )
            )
            await interaction.message.edit(
                content="Choose a name for your character in the pop-up.", view=None
            )
            self.stop()
            return
        if not self.saved_progress.get("farm_name"):
            await interaction.response.send_modal(
                FarmNameModal(
                    self.owner_id,
                    interaction.message,
                    self.saved_progress["character_name"],
                    resume_progress=self.saved_progress,
                )
            )
            await interaction.message.edit(
                content="Choose a name for your farm in the pop-up.", view=None
            )
            self.stop()
            return
        view = BodyView.restore(self.owner_id, self.saved_progress)
        if view is None:
            await interaction.response.edit_message(
                content="No body images found in assets/bodies.", view=None
            )
            return

        view.message = interaction.message
        await interaction.response.edit_message(
            content=None, attachments=[view.current()], view=view
        )
        colors = ColorView(self.owner_id, view)
        if "eyes" in view.step_images:
            colors.add_eye_color_button()
        if "bangs" in view.step_images:
            colors.add_hair_color_button()
        if "shirt" in view.step_images:
            colors.add_shirt_color_button()
        colors.update_stage_buttons(view.stage, view.step_images)
        colors.message = await view.message.reply("Colors", view=colors)
        view.colors = colors

    @discord.ui.button(label="Start Over", style=discord.ButtonStyle.danger)
    async def start_over(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        delete_progress(self.owner_id)
        menu = MainMenuView(self.owner_id)
        await interaction.response.edit_message(
            content=menu.status,
            attachments=[
                discord.File(render_main_menu(menu.selection), filename="main_menu.png")
            ],
            view=menu,
        )
        self.stop()


def save_farm_profile(owner_id: int, farm_name: str) -> dict:
    saved = read_progress(owner_id) or {}
    saved.update(
        {
            "farm_name": farm_name,
            "coins": int(saved.get("coins", 0)),
            "daily_earnings": int(saved.get("daily_earnings", 0)),
            "day": int(saved.get("day", 1)),
            "season": saved.get("season", "Spring"),
            "year": int(saved.get("year", 1)),
        }
    )
    write_progress(owner_id, saved)
    return saved


async def begin_portrait_creation(
    message: discord.Message,
    owner_id: int,
    saved_progress: dict | None = None,
) -> None:
    if saved_progress is not None:
        saved_progress = {**saved_progress, **(read_progress(owner_id) or {})}
    if saved_progress and saved_progress.get("steps"):
        view = BodyView.restore(owner_id, saved_progress)
    else:
        gender = (saved_progress or {}).get("gender", "feminine")
        images = load_body_images(gender)
        view = BodyView(
            owner_id,
            images,
            (saved_progress or {}).get("character_name", ""),
            gender,
        ) if images else None
    if view is None:
        gender = (saved_progress or {}).get("gender", "feminine")
        body_dir = (
            MASCULINE_BODY_DIR
            if gender == "masculine"
            else BODY_DIR
        )
        await message.edit(
            content=f"No body images found in {body_dir.relative_to(Path(__file__).parent)}.",
            view=None,
        )
        return
    view.message = await message.edit(
        content=None, attachments=[view.current()], view=view
    )
    colors = ColorView(owner_id, view)
    if "eyes" in view.step_images:
        colors.add_eye_color_button()
    if "bangs" in view.step_images:
        colors.add_hair_color_button()
    if "shirt" in view.step_images:
        colors.add_shirt_color_button()
    colors.update_stage_buttons(view.stage, view.step_images)
    colors.message = await view.message.reply("Colors", view=colors)
    view.colors = colors
    view.save_progress()


class CharacterNameModal(discord.ui.Modal, title="Name your character"):
    def __init__(
        self,
        owner_id: int,
        start_message: discord.Message | None,
        initial_name: str = "",
        launch_portrait: bool = True,
        resume_progress: dict | None = None,
    ) -> None:
        super().__init__()
        self.owner_id = owner_id
        self.start_message = start_message
        self.launch_portrait = launch_portrait
        self.resume_progress = resume_progress
        self.name_input = discord.ui.TextInput(
            label="Character name",
            placeholder="Enter a name",
            default=initial_name[:24] or None,
            min_length=1,
            max_length=24,
        )
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        character_name = self.name_input.value.strip()
        if not character_name:
            await interaction.response.send_message(
                "Enter a character name first.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Your character will be named **{character_name}**. Are you sure?",
            view=ConfirmCharacterNameView(
                self.owner_id,
                character_name,
                self.start_message,
                self.launch_portrait,
                self.resume_progress,
            ),
            ephemeral=True,
        )


class ConfirmCharacterNameView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        character_name: str,
        start_message: discord.Message | None,
        launch_portrait: bool = True,
        resume_progress: dict | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.character_name = character_name
        self.start_message = start_message
        self.launch_portrait = launch_portrait
        self.resume_progress = resume_progress

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This name confirmation is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not self.launch_portrait:
            saved = read_progress(self.owner_id) or {}
            write_progress(
                self.owner_id,
                {**saved, "character_name": self.character_name},
            )
            await interaction.response.edit_message(
                content=f"Name saved: {self.character_name}", view=None
            )
            self.stop()
            return
        saved = read_progress(self.owner_id) or {}
        saved["character_name"] = self.character_name
        write_progress(self.owner_id, saved)
        if not saved.get("farm_name"):
            await interaction.response.send_modal(
                FarmNameModal(
                    self.owner_id,
                    self.start_message,
                    self.character_name,
                    resume_progress=self.resume_progress,
                )
            )
            if self.start_message is not None:
                await self.start_message.edit(
                    content="Choose a name for your farm in the pop-up.", view=None
                )
        else:
            await interaction.response.edit_message(
                content=f"Name confirmed: {self.character_name}", view=None
            )
            if self.start_message is not None:
                await begin_portrait_creation(
                    self.start_message,
                    self.owner_id,
                    self.resume_progress or saved,
                )
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(
            CharacterNameModal(
                self.owner_id,
                self.start_message,
                self.character_name,
                self.launch_portrait,
                self.resume_progress,
            )
        )
        self.stop()


class FarmNameModal(discord.ui.Modal, title="Name your farm"):
    def __init__(
        self,
        owner_id: int,
        start_message: discord.Message | None,
        character_name: str = "",
        initial_name: str = "",
        launch_portrait: bool = True,
        resume_progress: dict | None = None,
    ) -> None:
        super().__init__()
        self.owner_id = owner_id
        self.start_message = start_message
        self.character_name = character_name
        self.launch_portrait = launch_portrait
        self.resume_progress = resume_progress
        self.name_input = discord.ui.TextInput(
            label="Farm name",
            placeholder="Enter a farm name",
            default=initial_name[:24] or None,
            min_length=1,
            max_length=24,
        )
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        farm_name = self.name_input.value.strip()
        if not farm_name:
            await interaction.response.send_message(
                "Enter a farm name first.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Your farm will be named **{farm_name}**. Are you sure?",
            view=ConfirmFarmNameView(
                self.owner_id,
                farm_name,
                self.start_message,
                self.character_name,
                self.launch_portrait,
                self.resume_progress,
            ),
            ephemeral=True,
        )


class ConfirmFarmNameView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        farm_name: str,
        start_message: discord.Message | None,
        character_name: str = "",
        launch_portrait: bool = True,
        resume_progress: dict | None = None,
    ) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.farm_name = farm_name
        self.start_message = start_message
        self.character_name = character_name
        self.launch_portrait = launch_portrait
        self.resume_progress = resume_progress

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This farm-name confirmation is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        saved = save_farm_profile(self.owner_id, self.farm_name)
        if self.character_name:
            saved["character_name"] = self.character_name
            write_progress(self.owner_id, saved)
        if self.launch_portrait and self.start_message is not None:
            await interaction.response.edit_message(
                content=f"Farm name confirmed: {self.farm_name}", view=None
            )
            self.stop()
            await begin_portrait_creation(
                self.start_message,
                self.owner_id,
                self.resume_progress or saved,
            )
            return
        await interaction.response.edit_message(
            content=f"Farm name saved: {self.farm_name}", view=None
        )
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(
            FarmNameModal(
                self.owner_id,
                self.start_message,
                self.character_name,
                self.farm_name,
                self.launch_portrait,
                self.resume_progress,
            )
        )
        self.stop()


class SetFarmNameView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This farm-name prompt is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Choose farm name", style=discord.ButtonStyle.primary)
    async def choose_name(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(
            FarmNameModal(
                self.owner_id,
                None,
                launch_portrait=False,
            )
        )
        await interaction.message.edit(view=None)
        self.stop()


class MainMenuArrow(discord.ui.Button):
    def __init__(self, direction: int) -> None:
        super().__init__(
            label="◀" if direction < 0 else "▶",
            style=discord.ButtonStyle.secondary,
            row=0,
        )
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        view: MainMenuView = self.view
        view.selection = (view.selection + self.direction) % 3
        view.selection_label.label = view.OPTIONS[view.selection]
        await interaction.response.edit_message(
            content=view.status,
            attachments=[
                discord.File(
                    render_main_menu(view.selection), filename="main_menu.png"
                )
            ],
            view=view,
        )


class MainMenuSelectionLabel(discord.ui.Button):
    def __init__(self, label: str) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.success, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.confirm_selection(interaction)


class MainMenuView(discord.ui.View):
    OPTIONS = ("New", "Load", "Exit")

    def __init__(self, owner_id: int, selection: int = 0) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.selection = selection % len(self.OPTIONS)
        self.add_item(MainMenuArrow(-1))
        self.selection_label = MainMenuSelectionLabel(self.OPTIONS[self.selection])
        self.add_item(self.selection_label)
        self.add_item(MainMenuArrow(1))

    @property
    def status(self) -> str:
        return "Choose an option"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This menu belongs to someone else.", ephemeral=True
            )
            return False
        return True

    async def confirm_selection(self, interaction: discord.Interaction) -> None:
        if self.selection == 0:
            await interaction.response.edit_message(
                content="Are you sure you want to restart your save file?",
                view=ConfirmNewGameView(self.owner_id),
            )
            self.stop()
            return
        if self.selection == 1:
            saved = read_progress(self.owner_id)
            if saved is None:
                await interaction.response.send_message(
                    "No save file was found.", ephemeral=True
                )
                return
            if saved.get("phase") == "arrival":
                saved.pop("farm", None)
                write_progress(self.owner_id, saved)
                await interaction.response.edit_message(
                    content="Now it's time to choose your farm!",
                    attachments=[],
                    view=None,
                )
                await show_farm_picker(interaction.message, self.owner_id)
                self.stop()
                return
            portrait_path = PROGRESS_FILE.parent / "portraits" / f"{self.owner_id}.png"
            profile_complete = saved.get("completed") or portrait_path.is_file()
            if profile_complete:
                saved.pop("farm", None)
                saved.pop("pending_farm", None)
                write_progress(self.owner_id, saved)
                await interaction.response.edit_message(
                    content="Now it's time to choose your farm!", view=None
                )
                await show_farm_picker(interaction.message, self.owner_id)
                self.stop()
                return
            await interaction.response.edit_message(
                content="Loading your save file.", attachments=[], view=None
            )
            await begin_portrait_creation(interaction.message, self.owner_id, saved)
            self.stop()
            return
        await interaction.response.edit_message(
            content="Goodbye, hope to see you soon.", attachments=[], view=None
        )
        self.stop()


class ConfirmNewGameView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This restart confirmation is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def yes(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        delete_character_save(self.owner_id)
        await interaction.response.edit_message(
            content="Choose your character's body type.",
            attachments=[],
            view=GenderSelectionView(self.owner_id),
        )
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        menu = MainMenuView(self.owner_id)
        await interaction.response.edit_message(
            content=menu.status,
            attachments=[discord.File(render_main_menu(menu.selection), filename="main_menu.png")],
            view=menu,
        )
        self.stop()


class GenderSelectionView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This character setup belongs to someone else.", ephemeral=True
            )
            return False
        return True

    async def choose_gender(
        self, interaction: discord.Interaction, gender: str
    ) -> None:
        saved = read_progress(self.owner_id) or {}
        write_progress(self.owner_id, {**saved, "gender": gender})
        await interaction.response.send_modal(
            CharacterNameModal(self.owner_id, interaction.message)
        )
        await interaction.message.edit(
            content="Choose a name for your character in the pop-up.",
            attachments=[],
            view=None,
        )
        self.stop()

    @discord.ui.button(label="Feminine", style=discord.ButtonStyle.primary)
    async def feminine(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.choose_gender(interaction, "feminine")

    @discord.ui.button(label="Masculine", style=discord.ButtonStyle.primary)
    async def masculine(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.choose_gender(interaction, "masculine")


class SetCharacterNameView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This name prompt is not for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Choose name", style=discord.ButtonStyle.primary)
    async def choose_name(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(
            CharacterNameModal(
                self.owner_id,
                None,
                launch_portrait=False,
            )
        )
        await interaction.message.edit(view=None)
        self.stop()


class FarmBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.content.strip().lower() == "s!inv":
            saved = read_progress(message.author.id) or {}
            portrait_path = (
                Path(__file__).parent
                / "data"
                / "portraits"
                / f"{message.author.id}.png"
            )
            if not portrait_path.is_file():
                body_dir = (
                    MASCULINE_BODY_DIR
                    if saved.get("gender") == "masculine"
                    else BODY_DIR
                )
                portrait_path = body_dir / "1.png"
            view = InventoryTestView(
                message.author.id,
                saved.get("character_name") or message.author.display_name,
                int(saved.get("level", 1)),
                int(saved.get("coins", 0)),
                portrait_path,
                saved.get("farm_name") or "Farm",
                int(saved.get("daily_earnings", 0)),
                int(saved.get("day", 1)),
                saved.get("season", "Spring"),
                int(saved.get("year", 1)),
            )
            await message.reply(
                content=view.status,
                file=discord.File(view.render(), filename="inventory.png"),
                view=view,
            )
            return

        if message.content.strip().lower() == "s!name":
            saved = read_progress(message.author.id) or {}
            existing_name = saved.get("character_name", "").strip()
            if existing_name:
                await message.reply(
                    f"You already chose the name {existing_name}."
                )
                return
            await message.reply(
                "Choose a name for your character.",
                view=SetCharacterNameView(message.author.id),
            )
            return

        if message.content.strip().lower() == "s!farmname":
            saved = read_progress(message.author.id) or {}
            existing_name = saved.get("farm_name", "").strip()
            if existing_name:
                await message.reply(
                    f"Your farm is already named {existing_name}."
                )
                return
            await message.reply(
                "Choose a name for your farm.",
                view=SetFarmNameView(message.author.id),
            )
            return

        if message.content.strip().lower() == "p!test":
            view = FishingVersionSelectView(message.author.id)
            await message.reply(
                content="Choose a fishing difficulty version:",
                view=view,
            )
            return

        if message.content.strip().lower() == "s!test":
            if not ROOM_IMAGE.is_file() or not BED_IMAGE.is_file():
                await message.reply(
                    "Room or bed image is missing. Expected room_edits/image.png "
                    "and room_edits/bed.png."
                )
                return
            view = RoomTestView(message.author.id, ROOM_IMAGE, BED_IMAGE)
            await message.reply(
                file=discord.File(view.render(), filename="room_test.png"),
                view=view,
            )
            return

        if self.user not in message.mentions:
            return

        text = MENTION_PATTERN.sub("", message.content).strip().lower()
        if text == "farm":
            reply = await message.reply("Now it's time to choose your farm!")
            await asyncio.sleep(3)
            await show_farm_picker(reply, message.author.id)
            return
        if text == "start":
            menu = MainMenuView(message.author.id)
            await message.reply(
                content=menu.status,
                file=discord.File(render_main_menu(menu.selection), filename="main_menu.png"),
                view=menu,
            )
