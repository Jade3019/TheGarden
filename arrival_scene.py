import asyncio
import io
from pathlib import Path

import discord
from PIL import Image, ImageChops, ImageDraw, ImageEnhance

PROJECT_DIR = Path(__file__).parent
BUS_STOP_IMAGE = PROJECT_DIR / "stardew places" / "day spring" / "bus_stop_spring_day.png"
DIALOGUE_FRAME = PROJECT_DIR / "character.assets" / "dialogue_box_frame.png"
HAPPY_LEWIS = PROJECT_DIR / "Characters" / "Lewis" / "Happy_lewis.png"

GLYPHS = {
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "f": ("00110", "01001", "01000", "11100", "01000", "01000", "01000"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10011", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
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


ARRIVAL_TEXT = "You finally arrived!"
TEXT_X = 56
TEXT_SCALE = 5
REVEAL_EDGE = 40


def _text_width(text: str, scale: int) -> int:
    return sum(4 * scale if character == " " else 6 * scale for character in text)


def arrival_scene(reveal: float | None = None) -> io.BytesIO:
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

    lewis = Image.open(HAPPY_LEWIS).convert("RGBA")
    lewis = lewis.resize((lewis.width * 2, lewis.height * 2), Image.Resampling.NEAREST)
    scene.alpha_composite(lewis, (40, frame_top + solid_row - lewis.height))

    if reveal is not None:
        text_layer = Image.new("RGBA", scene.size, (0, 0, 0, 0))
        text_top = frame_top + 44
        _draw_text(text_layer, ARRIVAL_TEXT, TEXT_X, text_top, TEXT_SCALE)
        text_width = _text_width(ARRIVAL_TEXT, TEXT_SCALE)
        front = TEXT_X + (text_width + REVEAL_EDGE) * reveal
        mask = Image.new("L", scene.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        for x in range(TEXT_X, TEXT_X + text_width + 1):
            strength = max(0.0, min(1.0, (front - x) / REVEAL_EDGE))
            mask_draw.line((x, text_top, x, text_top + 8 * TEXT_SCALE), fill=round(strength * 255))
        text_layer.putalpha(ImageChops.multiply(text_layer.getchannel("A"), mask))
        scene.alpha_composite(text_layer)
    return _to_bytes(scene)


async def play_arrival(
    message: discord.Message, picker_image: Image.Image, step_delay: float = 1.0
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
        await message.edit(attachments=attachment(arrival_scene(reveal)))
        await asyncio.sleep(step_delay * 0.5)
