import io
import math
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps


ITEMS_PER_PAGE = 36
GRID_COLUMNS = 12
GRID_ROWS = 3
TEST_ITEMS = [f"Test Item {index + 1:02d}" for index in range(ITEMS_PER_PAGE)]
ITEM_COLORS = [
    (92, 164, 108),
    (91, 145, 194),
    (190, 136, 83),
    (171, 111, 177),
    (210, 172, 82),
    (90, 173, 165),
]


class InventoryTestPageButton(discord.ui.Button):
    def __init__(self, label: str, delta: int, row: int = 0) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryTestView = self.view
        view.page = max(0, min(view.page_count - 1, view.page + self.delta))
        view.selected_item_index = None
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory_test.png")],
            view=view,
        )


class InventoryTestDeleteButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Delete selected",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            row=0,
            disabled=True,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryTestView = self.view
        if view.selected_item_index is None:
            await interaction.response.send_message(
                "Select an item to delete first.", ephemeral=True
            )
            return
        del view.items[view.selected_item_index]
        view.selected_item_index = None
        view.page_count = max(
            2, math.ceil(len(view.items) / ITEMS_PER_PAGE)
        )
        view.page = min(view.page, view.page_count - 1)
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory_test.png")],
            view=view,
        )


class InventoryTestItemSelect(discord.ui.Select):
    def __init__(
        self, view: "InventoryTestView", start: int, end: int, row: int
    ) -> None:
        page_start = view.page * ITEMS_PER_PAGE
        options = [
            discord.SelectOption(label=item, value=str(index))
            for index, item in enumerate(view.items[page_start + start : page_start + end], page_start + start)
        ]
        self.empty = not options
        if not options:
            options = [discord.SelectOption(label="No items", value="none")]
        super().__init__(
            placeholder="Choose an item to delete",
            min_values=1,
            max_values=1,
            options=options,
            row=row,
            disabled=self.empty,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryTestView = self.view
        if self.values[0] == "none":
            await interaction.response.defer()
            return
        view.selected_item_index = int(self.values[0])
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory_test.png")],
            view=view,
        )


class InventoryTestView(discord.ui.View):
    width = 720
    height = 500

    def __init__(
        self,
        owner_id: int,
        character_name: str,
        level: int,
        coins: int,
        portrait_path: Path,
    ) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.character_name = character_name
        self.level = level
        self.coins = coins
        self.portrait_path = portrait_path
        self.items = TEST_ITEMS.copy()
        self.page = 0
        self.page_count = 2
        self.selected_item_index: int | None = None
        self.previous_button = InventoryTestPageButton("Previous", -1)
        self.next_button = InventoryTestPageButton("Next", 1)
        self.delete_button = InventoryTestDeleteButton()
        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        self.add_item(self.delete_button)
        self.first_select: InventoryTestItemSelect
        self.second_select: InventoryTestItemSelect
        self.rebuild_selects()

    @property
    def status(self) -> str:
        return f"Test inventory | Page {self.page + 1} of {self.page_count}"

    def rebuild_selects(self) -> None:
        if hasattr(self, "first_select"):
            self.remove_item(self.first_select)
            self.remove_item(self.second_select)
        self.first_select = InventoryTestItemSelect(self, 0, 25, row=1)
        self.second_select = InventoryTestItemSelect(
            self, 25, ITEMS_PER_PAGE, row=2
        )
        self.add_item(self.first_select)
        self.add_item(self.second_select)

    def refresh_controls(self) -> None:
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.page_count - 1
        self.delete_button.disabled = self.selected_item_index is None
        self.rebuild_selects()

    def render(self) -> io.BytesIO:
        image = Image.new("RGBA", (self.width, self.height), (57, 53, 63, 255))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=18)
        small_font = ImageFont.load_default(size=14)
        draw.rounded_rectangle((12, 12, 708, 238), radius=6, fill=(103, 72, 48), outline=(213, 156, 86), width=4)
        draw.rounded_rectangle((20, 20, 700, 230), radius=3, fill=(240, 181, 112), outline=(255, 218, 157), width=3)
        cell, gap = 48, 6
        grid_width = GRID_COLUMNS * cell + (GRID_COLUMNS - 1) * gap
        left = (self.width - grid_width) // 2
        top = 34
        for index in range(GRID_ROWS * GRID_COLUMNS):
            row, column = divmod(index, GRID_COLUMNS)
            x = left + column * (cell + gap)
            y = top + row * (cell + gap)
            draw.rectangle((x, y, x + cell, y + cell), fill=(255, 203, 139), outline=(255, 238, 196), width=2)
            item_index = self.page * ITEMS_PER_PAGE + index
            if item_index < len(self.items):
                color = ITEM_COLORS[item_index % len(ITEM_COLORS)]
                draw.ellipse((x + 11, y + 10, x + 37, y + 36), fill=color, outline=(94, 61, 47), width=2)
                draw.rectangle((x + 20, y + 8, x + 28, y + 15), fill=(242, 220, 149))
                if item_index == self.selected_item_index:
                    draw.rectangle((x + 2, y + 2, x + cell - 2, y + cell - 2), outline=(71, 179, 92), width=4)

        draw.rounded_rectangle((12, 248, 708, 488), radius=6, fill=(103, 72, 48), outline=(213, 156, 86), width=4)
        draw.rounded_rectangle((20, 256, 700, 480), radius=3, fill=(240, 181, 112), outline=(255, 218, 157), width=3)
        profile = Image.new("RGBA", (124, 142), (82, 142, 173, 255))
        if self.portrait_path.is_file():
            with Image.open(self.portrait_path) as source:
                portrait = source.convert("RGBA")
        else:
            with Image.open(Path(__file__).parent / "assets" / "bodies" / "1.png") as source:
                portrait = source.convert("RGBA")
        portrait = ImageOps.contain(portrait, (116, 134), Image.Resampling.NEAREST)
        profile.alpha_composite(portrait, ((124 - portrait.width) // 2, (142 - portrait.height) // 2))
        image.alpha_composite(profile, (30, 266))
        draw.rectangle((30, 266, 154, 408), outline=(112, 66, 45), width=3)

        coin_x, coin_y = 190, 286
        draw.ellipse((coin_x, coin_y, coin_x + 28, coin_y + 28), fill=(244, 192, 61), outline=(132, 81, 39), width=3)
        draw.text((coin_x + 38, coin_y + 5), f"Coins: {self.coins}", font=font, fill=(64, 43, 39))
        draw.text((30, 423), self.character_name[:24], font=font, fill=(64, 43, 39))
        draw.text((190, 423), f"Level {self.level}", font=font, fill=(64, 43, 39))
        draw.text((190, 322), "TEST INVENTORY", font=small_font, fill=(91, 63, 50))

        trash_x, trash_y = 624, 300
        draw.rectangle((trash_x + 8, trash_y + 12, trash_x + 33, trash_y + 44), fill=(177, 178, 176), outline=(78, 75, 76), width=3)
        draw.rectangle((trash_x + 3, trash_y + 7, trash_x + 38, trash_y + 13), fill=(204, 204, 199), outline=(78, 75, 76), width=2)
        draw.line((trash_x + 15, trash_y + 18, trash_x + 15, trash_y + 38), fill=(82, 80, 78), width=2)
        draw.line((trash_x + 25, trash_y + 18, trash_x + 25, trash_y + 38), fill=(82, 80, 78), width=2)
        draw.text((610, 356), "Trash", font=small_font, fill=(64, 43, 39))

        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This test inventory belongs to someone else.", ephemeral=True
            )
            return False
        return True
