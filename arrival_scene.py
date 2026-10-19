import asyncio
import io
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageEnhance

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


def arrival_scene(with_text: bool) -> io.BytesIO:
    scene = Image.open(BUS_STOP_IMAGE).convert("RGBA")
    frame = Image.open(DIALOGUE_FRAME).convert("RGBA")
    frame_height = round(frame.height * scene.width / frame.width)
    frame = frame.resize((scene.width, frame_height), Image.Resampling.NEAREST)
    frame_top = scene.height - frame_height
    scene.alpha_composite(frame, (0, frame_top))

    lewis = Image.open(HAPPY_LEWIS).convert("RGBA")
    lewis = lewis.resize((lewis.width * 2, lewis.height * 2), Image.Resampling.NEAREST)
    lewis_x = 40
    lewis_y = frame_top - lewis.height
    scene.alpha_composite(lewis, (lewis_x, lewis_y))

    if with_text:
        _draw_text(scene, "You finally arrived!", 56, frame_top + 44, 5)
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
    await message.edit(attachments=attachment(arrival_scene(False)))
    await asyncio.sleep(step_delay)
    await message.edit(attachments=attachment(arrival_scene(True)))
