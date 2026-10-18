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
FARM_DIR = PROJECT_DIR / "assets" / "farms"


class FarmerTestButton(discord.ui.Button):
    def __init__(self, label: str, action: str, delta: int = 0, row: int = 0) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.action = action
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FarmerXnbTestView = self.view
        if self.action in {"name", "farm_name", "favorite_thing"}:
            await interaction.response.send_modal(FarmerTestModal(view, self.action))
            return
        if self.action == "gender":
            view.gender = (view.gender + 1) % len(BASE_SHEETS)
        elif self.action == "skin":
            view.skin = (view.skin + self.delta) % 24
        elif self.action == "hair":
            view.hair = (view.hair + self.delta) % (8 * 21)
        elif self.action == "farm":
            view.farm = (view.farm + self.delta) % 8
        elif self.action == "shirt":
            view.shirt = max(1, (view.shirt + self.delta - 1) % 112 + 1)
        elif self.action == "pants":
            view.pants = max(1, (view.pants + self.delta - 1) % 112 + 1)
        elif self.action == "accessory":
            view.accessory = max(1, (view.accessory + self.delta - 1) % 20 + 1)
        elif self.action == "finish":
            view.stop()
            await interaction.response.edit_message(
                content="Farmer XNB test complete. Nothing was saved.",
                attachments=[],
                view=None,
            )
            return
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="farmer_test.png")],
            view=view,
        )


class FarmerTestModal(discord.ui.Modal):
    def __init__(self, view: "FarmerXnbTestView", field: str) -> None:
        titles = {
            "name": "Character name",
            "farm_name": "Farm name",
            "favorite_thing": "Favorite thing",
        }
        super().__init__(title=titles[field])
        self.farmer_view = view
        self.field = field
        self.value_input = discord.ui.TextInput(
            label=titles[field],
            placeholder=f"Enter {titles[field].lower()}",
            default=getattr(view, field)[:24] or None,
            max_length=24,
            required=False,
        )
        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        setattr(self.farmer_view, self.field, self.value_input.value.strip())
        await interaction.response.send_message(
            f"Updated {self.value_input.label.lower()}.", ephemeral=True
        )
        if self.farmer_view.message is not None:
            await self.farmer_view.message.edit(
                content=self.farmer_view.status,
                attachments=[
                    discord.File(
                        self.farmer_view.render(), filename="farmer_test.png"
                    )
                ],
                view=self.farmer_view,
            )


class FarmerXnbTestView(discord.ui.View):
    width = 900
    height = 520

    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.name = ""
        self.farm_name = ""
        self.favorite_thing = ""
        self.message: discord.Message | None = None
        self.gender = 0
        self.skin = 0
        self.hair = 0
        self.farm = 0
        self.shirt = 1
        self.pants = 1
        self.accessory = 1
        for label, action, row in (
            ("Name", "name", 0),
            ("Farm Name", "farm_name", 0),
            ("Favorite Thing", "favorite_thing", 0),
            ("Gender", "gender", 1),
            ("Skin -", "skin", 1),
            ("Skin +", "skin", 1),
            ("Hair -", "hair", 2),
            ("Hair +", "hair", 2),
            ("Farm -", "farm", 2),
            ("Farm +", "farm", 2),
            ("Shirt -", "shirt", 3),
            ("Shirt +", "shirt", 3),
            ("Pants -", "pants", 3),
            ("Pants +", "pants", 3),
            ("Acc. -", "accessory", 4),
            ("Acc. +", "accessory", 4),
            ("OK", "finish", 4),
        ):
            delta = -1 if label.endswith("-") else 1 if label.endswith("+") else 0
            self.add_item(FarmerTestButton(label, action, delta, row))

    @property
    def status(self) -> str:
        return "Farmer XNB test | Nothing is saved"

    def farmer_sprite(self) -> Image.Image:
        sheet = Image.open(BASE_SHEETS[self.gender]).convert("RGBA")
        farmer = sheet.crop((0, 0, 16, 32))
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

        hair_sheet = Image.open(HAIR_SHEET).convert("RGBA")
        hair_column = self.hair % 8
        hair_row = self.hair // 8
        hair = hair_sheet.crop(
            (hair_column * 16, hair_row * 32, (hair_column + 1) * 16, (hair_row + 1) * 32)
        )
        gray = ImageOps.grayscale(hair)
        tinted = ImageOps.colorize(gray, (35, 26, 31), (139, 87, 57)).convert("RGBA")
        tinted.putalpha(hair.getchannel("A"))
        farmer.alpha_composite(tinted)
        return farmer.resize((160, 320), Image.Resampling.NEAREST)

    def render(self) -> io.BytesIO:
        image = Image.new("RGBA", (self.width, self.height), (39, 117, 181, 255))
        draw = ImageDraw.Draw(image)
        for x, y, scale in ((35, 370, 1), (742, 75, 1), (775, 330, 1), (320, 25, 1)):
            draw.ellipse((x, y, x + 95 * scale, y + 38 * scale), fill=(219, 235, 245, 255))
            draw.ellipse((x + 18, y - 20, x + 62, y + 22), fill=(232, 243, 249, 255))
            draw.ellipse((x + 49, y - 13, x + 93, y + 28), fill=(232, 243, 249, 255))

        draw.rectangle((30, 42, 708, 480), fill=(130, 74, 37), outline=(227, 153, 67), width=5)
        draw.rectangle((40, 52, 698, 470), fill=(247, 190, 126), outline=(255, 222, 168), width=4)
        draw.rectangle((72, 92, 220, 388), fill=(108, 173, 208), outline=(111, 63, 37), width=5)
        farmer = self.farmer_sprite()
        image.alpha_composite(farmer, (80, 78))

        font = ImageFont.load_default(size=22)
        small = ImageFont.load_default(size=17)
        fields = (
            ("Name", self.name),
            ("Farm Name", self.farm_name),
            ("Favorite Thing", self.favorite_thing),
        )
        for index, (label, value) in enumerate(fields):
            y = 105 + index * 60
            draw.text((260, y + 5), label, font=font, fill=(130, 49, 43))
            draw.rectangle((402, y, 662, y + 40), fill=(255, 209, 148), outline=(143, 82, 45), width=3)
            draw.text((412, y + 11), value[:20], font=small, fill=(67, 43, 35))

        draw.text((260, 302), f"Gender: {'Male' if self.gender == 0 else 'Female'}", font=font, fill=(67, 43, 35))
        draw.text((260, 342), f"Skin {self.skin + 1}   Hair {self.hair + 1}", font=font, fill=(67, 43, 35))
        draw.text((260, 382), f"Shirt {self.shirt}   Pants {self.pants}   Acc. {self.accessory}", font=font, fill=(67, 43, 35))

        farm_names = (
            "Standard", "Riverland", "Forest", "Hill-top", "Wilderness",
            "Four Corners", "Beach", "Meadowlands",
        )
        for index, name in enumerate(farm_names):
            x, y = 742, 70 + index * 51
            farm_image = Image.open(FARM_DIR / f"{index + 1}.png").convert("RGBA")
            farm_image = ImageOps.fit(farm_image, (70, 44), Image.Resampling.NEAREST)
            image.alpha_composite(farm_image, (x, y))
            draw.rectangle((x, y, x + 70, y + 44), outline=(151, 82, 41), width=3)
            if index == self.farm:
                draw.rectangle((x - 3, y - 3, x + 73, y + 47), outline=(255, 220, 72), width=4)
        draw.text((742, 485), "Farmer XNB assets", font=small, fill=(248, 239, 209))

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
