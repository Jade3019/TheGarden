import io
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_DIR = Path(__file__).parent
FARMER_ASSETS = PROJECT_DIR / "character test" / "Farmer" / "decoded"
BASE_SHEETS = (
    FARMER_ASSETS / "farmer_base_bald.png",
    FARMER_ASSETS / "farmer_girl_base_bald.png",
)
HAIR_SHEET = FARMER_ASSETS / "hairstyles.png"
SKIN_PALETTE = FARMER_ASSETS / "skinColors.png"
HAIR_COLORS = (
    ((27, 22, 25), (91, 60, 42)),
    ((48, 29, 24), (137, 83, 51)),
    ((72, 41, 25), (181, 112, 59)),
    ((93, 47, 29), (207, 130, 71)),
    ((77, 57, 28), (225, 183, 92)),
    ((89, 78, 64), (213, 196, 165)),
    ((37, 45, 75), (91, 124, 191)),
    ((78, 40, 68), (180, 92, 151)),
)
EYE_COLORS = (
    (46, 32, 24),
    (43, 83, 131),
    (48, 116, 78),
    (111, 76, 45),
    (97, 83, 135),
    (48, 130, 139),
)
EYE_COLOR_NAMES = ("Brown", "Blue", "Green", "Hazel", "Violet", "Teal")
HAIR_COLOR_NAMES = (
    "Black",
    "Dark Brown",
    "Brown",
    "Auburn",
    "Blonde",
    "Silver",
    "Blue",
    "Violet",
)
CLOTHING_COLORS = (
    (55, 88, 171),
    (55, 139, 89),
    (172, 62, 58),
    (155, 93, 168),
    (205, 143, 51),
    (54, 151, 159),
    (56, 60, 72),
    (205, 178, 130),
)


class FarmerTestButton(discord.ui.Button):
    def __init__(self, label: str, action: str, delta: int = 0, row: int = 0) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.action = action
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FarmerXnbTestView = self.view
        if self.action == "gender":
            view.gender = (view.gender + 1) % len(BASE_SHEETS)
        elif self.action == "skin":
            view.skin = (view.skin + self.delta) % 24
        elif self.action == "eye_color":
            view.eye_color = (view.eye_color + self.delta) % len(EYE_COLORS)
        elif self.action == "hair":
            view.hair = (view.hair + self.delta) % (8 * 21)
        elif self.action == "hair_color":
            view.hair_color = (view.hair_color + self.delta) % len(HAIR_COLORS)
        elif self.action == "shirt":
            view.shirt = (view.shirt + self.delta) % len(CLOTHING_COLORS)
        elif self.action == "pants":
            view.pants = (view.pants + self.delta) % len(CLOTHING_COLORS)
        elif self.action == "accessory":
            view.accessory = (view.accessory + self.delta) % 8
        elif self.action == "finish":
            view.stop()
            await interaction.response.edit_message(
                content="Farmer character test complete. Nothing was saved.",
                attachments=[],
                view=None,
            )
            return
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="farmer_test.png")],
            view=view,
        )


class FarmerXnbTestView(discord.ui.View):
    width = 900
    height = 520

    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.message: discord.Message | None = None
        self.gender = 0
        self.skin = 0
        self.hair = 3
        self.eye_color = 0
        self.hair_color = 2
        self.shirt = 0
        self.pants = 0
        self.accessory = 0
        for label, action, row in (
            ("Gender", "gender", 0),
            ("Skin -", "skin", 0),
            ("Skin +", "skin", 0),
            ("Eye -", "eye_color", 0),
            ("Eye +", "eye_color", 0),
            ("Hair -", "hair", 1),
            ("Hair +", "hair", 1),
            ("Hair Color -", "hair_color", 1),
            ("Hair Color +", "hair_color", 1),
            ("Shirt -", "shirt", 2),
            ("Shirt +", "shirt", 2),
            ("Pants -", "pants", 2),
            ("Pants +", "pants", 2),
            ("Acc. -", "accessory", 3),
            ("Acc. +", "accessory", 3),
            ("Done", "finish", 3),
        ):
            delta = -1 if label.endswith("-") else 1 if label.endswith("+") else 0
            self.add_item(FarmerTestButton(label, action, delta, row))

    @property
    def status(self) -> str:
        return "Farmer XNB test | Nothing is saved"

    def farmer_sprite(self) -> Image.Image:
        sheet = Image.open(BASE_SHEETS[self.gender]).convert("RGBA")
        farmer = sheet.crop((48, 0, 64, 32))
        palette = Image.open(SKIN_PALETTE).convert("RGBA")
        defaults = [palette.getpixel((column, 0))[:3] for column in range(3)]
        selected = [palette.getpixel((column, self.skin))[:3] for column in range(3)]
        pixels = farmer.load()
        shade_map = dict(zip(defaults, selected))
        for y in range(farmer.height):
            for x in range(farmer.width):
                pixel = pixels[x, y]
                replacement = shade_map.get(pixel[:3])
                if replacement is not None:
                    pixels[x, y] = (*replacement, pixel[3])

        eye_color = EYE_COLORS[self.eye_color]
        for y in range(8, 15):
            for x in range(2, 14):
                if farmer.getpixel((x, y))[:3] == (15, 10, 8):
                    farmer.putpixel((x, y), (*eye_color, 255))

        draw = ImageDraw.Draw(farmer)
        shirt_color = CLOTHING_COLORS[self.shirt]
        shirt_shadow = tuple(round(channel * 0.62) for channel in shirt_color)
        draw.polygon(
            [(6, 15), (7, 14), (9, 14), (10, 15), (11, 17), (10, 21),
             (9, 22), (7, 22), (6, 21), (5, 17)],
            fill=shirt_color,
            outline=shirt_shadow,
        )
        pants_color = CLOTHING_COLORS[self.pants]
        pants_shadow = tuple(round(channel * 0.58) for channel in pants_color)
        draw.polygon(
            [(4, 22), (12, 22), (11, 28), (9, 28), (8, 25), (7, 28), (5, 28)],
            fill=pants_color,
            outline=pants_shadow,
        )
        accessory_color = CLOTHING_COLORS[(self.accessory + 3) % len(CLOTHING_COLORS)]
        draw.point((8, 17), fill=accessory_color)
        draw.point((7, 18), fill=accessory_color)
        draw.point((9, 18), fill=accessory_color)

        hair_sheet = Image.open(HAIR_SHEET).convert("RGBA")
        hair_column = self.hair % 8
        hair_row = self.hair // 8
        hair = hair_sheet.crop(
            (hair_column * 16, hair_row * 32, (hair_column + 1) * 16, (hair_row + 1) * 32)
        )
        gray = ImageOps.grayscale(hair)
        shadow, highlight = HAIR_COLORS[self.hair_color]
        tinted = ImageOps.colorize(gray, shadow, highlight).convert("RGBA")
        tinted.putalpha(hair.getchannel("A"))
        farmer.alpha_composite(tinted)
        return farmer.resize((160, 320), Image.Resampling.NEAREST)

    def render(self) -> io.BytesIO:
        image = Image.new("RGBA", (self.width, self.height), (39, 117, 181, 255))
        draw = ImageDraw.Draw(image)
        for x, y in ((35, 370), (742, 75), (775, 330), (320, 25)):
            draw.ellipse((x, y, x + 95, y + 38), fill=(219, 235, 245, 255))
            draw.ellipse((x + 18, y - 20, x + 62, y + 22), fill=(232, 243, 249, 255))
            draw.ellipse((x + 49, y - 13, x + 93, y + 28), fill=(232, 243, 249, 255))

        draw.rectangle((30, 42, 870, 480), fill=(130, 74, 37), outline=(227, 153, 67), width=5)
        draw.rectangle((40, 52, 860, 470), fill=(247, 190, 126), outline=(255, 222, 168), width=4)
        draw.rectangle((72, 92, 220, 388), fill=(108, 173, 208), outline=(111, 63, 37), width=5)
        farmer = self.farmer_sprite()
        image.alpha_composite(farmer, (80, 78))

        font = ImageFont.load_default(size=22)
        small = ImageFont.load_default(size=17)
        draw.text((285, 90), "Character", font=font, fill=(130, 49, 43))
        labels = (
            ("Gender", "Female" if self.gender else "Male"),
            ("Skin", f"{self.skin + 1}/24"),
            ("Eye Color", EYE_COLOR_NAMES[self.eye_color]),
            ("Hair", f"Style {self.hair + 1}"),
            ("Hair Color", HAIR_COLOR_NAMES[self.hair_color]),
            ("Shirt", f"Style {self.shirt + 1}"),
            ("Pants", f"Style {self.pants + 1}"),
            ("Accessories", f"{self.accessory + 1}"),
        )
        for index, (label, value) in enumerate(labels):
            y = 132 + index * 39
            draw.text((285, y + 6), label, font=small, fill=(130, 49, 43))
            draw.rounded_rectangle(
                (455, y, 795, y + 31),
                radius=3,
                fill=(255, 209, 148),
                outline=(143, 82, 45),
                width=2,
            )
            draw.text((467, y + 7), value, font=small, fill=(67, 43, 35))

        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This farmer test belongs to someone else.", ephemeral=True
            )
            return False
        return True
