import asyncio
import io
from pathlib import Path

import discord
from PIL import Image, ImageChops, ImageDraw, ImageEnhance

PROJECT_DIR = Path(__file__).parent
BUS_STOP_IMAGE = PROJECT_DIR / "stardew places" / "day spring" / "bus_stop_spring_day.png"
DIALOGUE_FRAME = PROJECT_DIR / "character.assets" / "dialogue_box_frame.png"
NORMAL_LEWIS = PROJECT_DIR / "Characters" / "Lewis" / "normal_lewis.png"
HAPPY_LEWIS = PROJECT_DIR / "Characters" / "Lewis" / "Happy_lewis.png"

GLYPHS = {
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "f": ("00110", "01001", "01000", "11100", "01000", "01000", "01000"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "h": ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "g": ("00000", "00000", "01111", "10001", "01111", "00001", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "w": ("00000", "00000", "10001", "10001", "10101", "10101", "01010"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01111", "10000", "10000", "10000", "01111"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "q": ("00000", "00000", "01101", "10011", "10001", "01111", "00001"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10011", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
}


def _to_bytes(image: Image.Image) -> io.BytesIO:
    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output


def fade_frame(image: Image.Image, brightness: float) -> io.BytesIO:
    return _to_bytes(ImageEnhance.Brightness(image.convert("RGB")).enhance(brightness))


def bus_stop_frame(brightness: float = 1.0) -> io.BytesIO:
    with Image.open(BUS_STOP_IMAGE) as source:
        return fade_frame(source, brightness)


def _draw_text(image: Image.Image, text: str, x: int, y: int, scale: int) -> None:
    draw = ImageDraw.Draw(image)
    cursor = x
    for character in text:
        if character == " ":
            cursor += 4 * scale
            continue
        for row, bits in enumerate(GLYPHS[character]):
            for column, bit in enumerate(bits):
                if bit != "1":
                    continue
                left = cursor + column * scale
                top = y + row * scale
                draw.rectangle(
                    (left + scale, top + scale, left + 2 * scale - 1, top + 2 * scale - 1),
                    fill=(222, 148, 77),
                )
                draw.rectangle(
                    (left, top, left + scale - 1, top + scale - 1),
                    fill=(105, 31, 14),
                )
        cursor += 6 * scale


ARRIVAL_TEXT = "You finally have arrived!"
JOURNEY_QUESTION = "I hope your journey went well."
JOURNEY_CHOICES = (
    "1. It went alright",
    "2. it went amazing, i cant wait to get started.",
    "3. it went horrible.",
)
TEXT_X = 56
TEXT_SCALE = 5
REVEAL_EDGE = 40


def _text_width(text: str, scale: int) -> int:
    return sum(4 * scale if character == " " else 6 * scale for character in text)


def _draw_wrapped_text(
    image: Image.Image, text: str, x: int, y: int, scale: int, max_width: int
) -> None:
    line_y = y
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and _text_width(candidate, scale) > max_width:
                _draw_text(image, line, x, line_y, scale)
                line_y += 9 * scale
                line = word
            else:
                line = candidate
        if line:
            _draw_text(image, line, x, line_y, scale)
        line_y += 9 * scale


def dialogue_scene(
    text: str,
    lewis_image: Path | None = None,
    player_portrait: Path | Image.Image | None = None,
    reveal: float | None = None,
    scale: int = 4,
) -> io.BytesIO:
    scene = Image.open(BUS_STOP_IMAGE).convert("RGBA")
    frame = Image.open(DIALOGUE_FRAME).convert("RGBA")
    frame_height = round(frame.height * scene.width / frame.width)
    frame = frame.resize((scene.width, frame_height), Image.Resampling.NEAREST)
    frame_top = scene.height - frame_height
    scene.alpha_composite(frame, (0, frame_top))
    # The frame's top rows are transparent, so Lewis stands on its first solid row.
    alpha = frame.getchannel("A")
    solid_row = next(
        row
        for row in range(frame.height)
        if sum(1 for x in range(0, frame.width, 8) if alpha.getpixel((x, row)) > 0)
        > frame.width // 16
    )

    if lewis_image is not None:
        lewis = Image.open(lewis_image).convert("RGBA")
        lewis = lewis.resize((lewis.width * 2, lewis.height * 2), Image.Resampling.NEAREST)
        lewis = lewis.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        scene.alpha_composite(lewis, (40, frame_top + solid_row - lewis.height))

    if player_portrait is not None:
        if isinstance(player_portrait, Image.Image):
            portrait = player_portrait.convert("RGBA")
        else:
            portrait = Image.open(player_portrait).convert("RGBA")
        portrait_draw = ImageDraw.Draw(portrait)
        transparent_white = (255, 255, 255, 0)
        edge_points = (
            [(x, 0) for x in range(portrait.width)]
            + [(x, portrait.height - 1) for x in range(portrait.width)]
            + [(0, y) for y in range(portrait.height)]
            + [(portrait.width - 1, y) for y in range(portrait.height)]
        )
        for point in edge_points:
            red, green, blue, alpha = portrait.getpixel(point)
            if alpha and red >= 245 and green >= 245 and blue >= 245:
                ImageDraw.floodfill(portrait, point, transparent_white, thresh=10)
        portrait = portrait.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        bounds = portrait.getchannel("A").getbbox()
        if bounds is not None:
            portrait = portrait.crop(bounds)
            target_height = 190
            target_width = round(portrait.width * target_height / portrait.height)
            portrait = portrait.resize(
                (target_width, target_height), Image.Resampling.NEAREST
            )
            scene.alpha_composite(
                portrait,
                (scene.width - target_width - 24, frame_top - target_height),
            )

    if reveal is not None:
        text_layer = Image.new("RGBA", scene.size, (0, 0, 0, 0))
        text_top = frame_top + 44
        _draw_wrapped_text(
            text_layer,
            text,
            TEXT_X,
            text_top,
            TEXT_SCALE,
            scene.width - TEXT_X - 44,
        )
        text_width = _text_width(text, TEXT_SCALE)
        front = TEXT_X + (text_width + REVEAL_EDGE) * reveal
        mask = Image.new("L", scene.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        for x in range(TEXT_X, min(scene.width, TEXT_X + text_width + 1)):
            strength = max(0.0, min(1.0, (front - x) / REVEAL_EDGE))
            mask_draw.line((x, text_top, x, text_top + 8 * TEXT_SCALE), fill=round(strength * 255))
        text_layer.putalpha(ImageChops.multiply(text_layer.getchannel("A"), mask))
        scene.alpha_composite(text_layer)
    else:
        text_top = frame_top + (28 if "\n" in text else 44)
        _draw_wrapped_text(
            scene,
            text,
            TEXT_X,
            text_top,
            scale,
            scene.width - TEXT_X - 44,
        )
    return _to_bytes(scene)


def arrival_scene(reveal: float | None = None) -> io.BytesIO:
    return dialogue_scene(ARRIVAL_TEXT, HAPPY_LEWIS, reveal=reveal, scale=TEXT_SCALE)


async def play_arrival(
    message: discord.Message,
    picker_image: Image.Image,
    step_delay: float = 1.0,
    completion_view: discord.ui.View | None = None,
) -> None:
    def attachment(data: io.BytesIO) -> list[discord.File]:
        return [discord.File(data, filename="scene.png")]

    await message.edit(content="Amazing choice!", view=None)
    for brightness in (0.5, 0.2, 0.0):
        await message.edit(attachments=attachment(fade_frame(picker_image, brightness)))
        await asyncio.sleep(step_delay)
    with Image.open(BUS_STOP_IMAGE) as bus_stop:
        for brightness in (0.2, 0.6, 1.0):
            await message.edit(
                content=None, attachments=attachment(fade_frame(bus_stop, brightness))
            )
            await asyncio.sleep(step_delay)
    await asyncio.sleep(step_delay * 3)
    await message.edit(attachments=attachment(arrival_scene()))
    await asyncio.sleep(step_delay)
    for reveal in (0.25, 0.5, 0.75, 1.0):
        await message.edit(
            attachments=attachment(arrival_scene(reveal)),
            view=completion_view if reveal == 1.0 else None,
        )
        await asyncio.sleep(step_delay * 0.15)
