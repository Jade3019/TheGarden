import io

from PIL import Image, ImageDraw


SCALE = 2
WIDTH = 480
HEIGHT = 270
PIXEL_FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10101", "10011", "10001", "10001"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
}


def _pixel_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, scale: int) -> None:
    glyph_width = 5
    spacing = 1
    total_width = sum(glyph_width + spacing for char in text) - spacing
    x = (WIDTH - total_width * scale) // 2
    for character in text:
        if character == " ":
            x += (glyph_width + spacing) * scale
            continue
        glyph = PIXEL_FONT[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    draw.rectangle(
                        (
                            x + column * scale,
                            y + row * scale,
                            x + (column + 1) * scale - 1,
                            y + (row + 1) * scale - 1,
                        ),
                        fill=(104, 61, 54),
                    )
        x += (glyph_width + spacing) * scale


def render_main_menu() -> io.BytesIO:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        color = (
            round(16 + 93 * ratio),
            round(74 + 121 * ratio),
            round(135 + 78 * ratio),
        )
        for x in range(WIDTH):
            pixels[x, y] = color

    draw = ImageDraw.Draw(image)
    cloud_groups = ((-10, 100), (12, 190), (380, 66), (408, 153), (274, 214))
    for x, y in cloud_groups:
        for dx, dy, width, height in (
            (0, 15, 72, 17), (17, 3, 24, 29), (36, 0, 28, 33),
            (60, 11, 32, 21), (24, 20, 56, 17),
        ):
            draw.ellipse(
                (x + dx, y + dy, x + dx + width, y + dy + height),
                fill=(220, 237, 247),
            )
        draw.rectangle((x + 8, y + 18, x + 79, y + 32), fill=(220, 237, 247))
        draw.line((x + 8, y + 31, x + 78, y + 31), fill=(184, 215, 234), width=2)

    draw.rectangle((0, 250, WIDTH, HEIGHT), fill=(69, 133, 74))
    draw.rectangle((0, 250, WIDTH, 255), fill=(99, 171, 83))
    for x in range(8, WIDTH, 19):
        draw.line((x, 258, x - 3, 249), fill=(123, 188, 87), width=2)
        if x % 3 == 0:
            draw.rectangle((x + 4, 262, x + 6, 264), fill=(237, 205, 111))

    draw.rounded_rectangle((48, 38, 432, 203), radius=8, fill=(94, 53, 39), outline=(242, 172, 77), width=4)
    draw.rectangle((56, 46, 424, 195), fill=(196, 127, 76), outline=(255, 211, 135), width=3)
    draw.rectangle((64, 54, 416, 187), fill=(244, 223, 186), outline=(145, 91, 58), width=3)
    for y in (78, 102, 126, 150, 174):
        draw.line((68, y, 412, y), fill=(221, 194, 155), width=2)
        draw.line((73, y + 3, 130, y + 3), fill=(250, 235, 210), width=1)
        draw.line((345, y + 3, 405, y + 3), fill=(250, 235, 210), width=1)

    for x, y, direction in ((80, 47, 1), (393, 48, -1), (60, 166, 1), (410, 164, -1)):
        draw.line((x, y, x + 13 * direction, y + 20), fill=(78, 131, 65), width=3)
        draw.ellipse((x + 2, y + 5, x + 12, y + 15), fill=(104, 164, 77))
        leaf_start = x + 7 * direction
        leaf_end = x + 17 * direction
        draw.ellipse((min(leaf_start, leaf_end), y + 11, max(leaf_start, leaf_end), y + 22), fill=(132, 181, 85))

    _pixel_text(draw, "THE GARDEN", 0, 99, 5)
    output = io.BytesIO()
    image.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.Resampling.NEAREST).save(output, format="PNG")
    output.seek(0)
    return output
