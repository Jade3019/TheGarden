import io
import math
from dataclasses import dataclass
from pathlib import Path

import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps


ITEMS_PER_PAGE = 36
ITEMS_PER_PICKER_PAGE = 24
GRID_COLUMNS = 12
GRID_ROWS = 3
ITEM_COLORS = [
    (92, 164, 108),
    (91, 145, 194),
    (190, 136, 83),
    (171, 111, 177),
    (210, 172, 82),
    (90, 173, 165),
]
EQUIPMENT_SLOTS = (
    "hat",
    "shirt",
    "pants",
    "accessory_left",
    "accessory_right",
    "shoes",
)
EQUIPMENT_CATEGORIES = {
    "hat": "hat",
    "shirt": "shirt",
    "dress": "shirt",
    "pants": "pants",
    "skirt": "pants",
    "shoes": "shoes",
    "accessory": "accessory",
}


@dataclass
class InventoryItem:
    name: str
    category: str
    portrait_layer: Path | None = None


class InventoryTestPageButton(discord.ui.Button):
    def __init__(self, label: str, delta: int, row: int = 0) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.delta = delta

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryTestView = self.view
        view.page = max(0, min(view.page_count - 1, view.page + self.delta))
        view.picker_page = 0
        view.selected_item_index = None
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory.png")],
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
        removed_item = view.items.pop(view.selected_item_index)
        for slot, equipped_item in view.equipped.items():
            if equipped_item is removed_item:
                view.equipped[slot] = None
        view.selected_item_index = None
        view.page_count = max(
            2, math.ceil(len(view.items) / ITEMS_PER_PAGE)
        )
        view.page = min(view.page, view.page_count - 1)
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory.png")],
            view=view,
        )


class InventoryTestEquipButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Equip selected",
            style=discord.ButtonStyle.success,
            row=0,
            disabled=True,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryTestView = self.view
        if view.selected_item_index is None:
            await interaction.response.send_message(
                "Select an item to equip first.", ephemeral=True
            )
            return
        item = view.items[view.selected_item_index]
        slot = view.slot_for(item.category)
        if slot is None:
            await interaction.response.send_message(
                "That item cannot be equipped.", ephemeral=True
            )
            return
        if slot.startswith("accessory"):
            slot = next(
                (name for name in ("accessory_left", "accessory_right") if view.equipped[name] is None),
                None,
            )
            if slot is None:
                await interaction.response.send_message(
                    "Both accessory slots are full.", ephemeral=True
                )
                return
        view.equipped[slot] = item
        view.selected_item_index = None
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory_test.png")],
            view=view,
        )


class InventoryTestItemSelect(discord.ui.Select):
    def __init__(self, view: "InventoryTestView") -> None:
        page_start = view.page * ITEMS_PER_PAGE
        page_end = min(page_start + ITEMS_PER_PAGE, len(view.items))
        picker_start = page_start + view.picker_page * ITEMS_PER_PICKER_PAGE
        picker_end = min(picker_start + ITEMS_PER_PICKER_PAGE, page_end)
        options = [
            discord.SelectOption(label=item.name[:100], value=str(index))
            for index, item in enumerate(
                view.items[picker_start:picker_end], picker_start
            )
        ]
        if view.picker_page > 0:
            options.insert(
                0,
                discord.SelectOption(label="Previous item choices", value="picker_previous"),
            )
        if picker_end < page_end:
            options.append(
                discord.SelectOption(label="More item choices", value="picker_next")
            )
        self.empty = not options
        if not options:
            options = [discord.SelectOption(label="No items", value="none")]
        super().__init__(
            placeholder="Choose an item",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
            disabled=self.empty,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryTestView = self.view
        if self.values[0] == "none":
            await interaction.response.defer()
            return
        if self.values[0] == "picker_next":
            view.picker_page += 1
            view.refresh_controls()
            await interaction.response.edit_message(
                content=view.status,
                attachments=[discord.File(view.render(), filename="inventory.png")],
                view=view,
            )
            return
        if self.values[0] == "picker_previous":
            view.picker_page = max(0, view.picker_page - 1)
            view.refresh_controls()
            await interaction.response.edit_message(
                content=view.status,
                attachments=[discord.File(view.render(), filename="inventory.png")],
                view=view,
            )
            return
        view.selected_item_index = int(self.values[0])
        view.refresh_controls()
        await interaction.response.edit_message(
            content=view.status,
            attachments=[discord.File(view.render(), filename="inventory.png")],
            view=view,
        )


class InventoryTestView(discord.ui.View):
    width = 720
    height = 540

    def __init__(
        self,
        owner_id: int,
        character_name: str,
        level: int,
        coins: int,
        portrait_path: Path,
        farm_name: str = "Farm",
        daily_earnings: int = 0,
        day: int = 1,
        season: str = "Spring",
        year: int = 1,
    ) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.character_name = character_name
        self.level = level
        self.coins = coins
        self.portrait_path = portrait_path
        self.farm_name = farm_name
        self.daily_earnings = daily_earnings
        self.day = day
        self.season = season
        self.year = year
        self.items: list[InventoryItem] = []
        self.equipped: dict[str, InventoryItem | None] = {
            slot: None for slot in EQUIPMENT_SLOTS
        }
        self.page = 0
        self.page_count = 2
        self.picker_page = 0
        self.selected_item_index: int | None = None
        self.previous_button = InventoryTestPageButton("Previous", -1)
        self.next_button = InventoryTestPageButton("Next", 1)
        self.delete_button = InventoryTestDeleteButton()
        self.equip_button = InventoryTestEquipButton()
        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        self.add_item(self.delete_button)
        self.add_item(self.equip_button)
        self.item_select: InventoryTestItemSelect
        self.rebuild_selector()

    @property
    def status(self) -> str:
        return f"Inventory | Page {self.page + 1} of {self.page_count}"

    def slot_for(self, category: str) -> str | None:
        return EQUIPMENT_CATEGORIES.get(category.strip().lower())

    def rebuild_selector(self) -> None:
        if hasattr(self, "item_select"):
            self.remove_item(self.item_select)
        self.item_select = InventoryTestItemSelect(self)
        self.add_item(self.item_select)

    def refresh_controls(self) -> None:
        self.page_count = max(2, math.ceil(len(self.items) / ITEMS_PER_PAGE))
        page_item_count = max(
            0,
            min(ITEMS_PER_PAGE, len(self.items) - self.page * ITEMS_PER_PAGE),
        )
        self.picker_page = min(
            self.picker_page,
            max(0, (page_item_count - 1) // ITEMS_PER_PICKER_PAGE),
        )
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.page_count - 1
        self.delete_button.disabled = self.selected_item_index is None
        self.equip_button.disabled = self.selected_item_index is None
        self.rebuild_selector()

    def render(self) -> io.BytesIO:
        image = Image.new("RGBA", (self.width, self.height), (57, 53, 63, 255))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=18)
        small_font = ImageFont.load_default(size=14)
        draw.rounded_rectangle((12, 12, 708, 210), radius=6, fill=(103, 72, 48), outline=(213, 156, 86), width=4)
        draw.rounded_rectangle((20, 20, 700, 202), radius=3, fill=(240, 181, 112), outline=(255, 218, 157), width=3)
        cell, gap = 48, 6
        grid_width = GRID_COLUMNS * cell + (GRID_COLUMNS - 1) * gap
        left = (self.width - grid_width) // 2
        top = 30
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

        draw.rounded_rectangle((12, 220, 708, 528), radius=6, fill=(103, 72, 48), outline=(213, 156, 86), width=4)
        draw.rounded_rectangle((20, 228, 700, 520), radius=3, fill=(240, 181, 112), outline=(255, 218, 157), width=3)
        profile = Image.new("RGBA", (124, 174), (82, 142, 173, 255))
        if self.portrait_path.is_file():
            with Image.open(self.portrait_path) as source:
                portrait = source.convert("RGBA")
        else:
            with Image.open(Path(__file__).parent / "assets" / "bodies" / "1.png") as source:
                portrait = source.convert("RGBA")
        portrait = ImageOps.fit(
            portrait,
            (116, 166),
            Image.Resampling.NEAREST,
            centering=(0.5, 0.5),
        )
        profile.alpha_composite(portrait, (4, 4))
        for slot in EQUIPMENT_SLOTS:
            item = self.equipped[slot]
            if item is not None and item.portrait_layer is not None and item.portrait_layer.is_file():
                with Image.open(item.portrait_layer) as source:
                    layer = source.convert("RGBA").resize(
                        profile.size, Image.Resampling.NEAREST
                    )
                profile.alpha_composite(layer)
        image.alpha_composite(profile, (84, 235))
        draw.rectangle((84, 235, 208, 409), outline=(112, 66, 45), width=3)

        slot_positions = {
            "hat": (22, 232),
            "shirt": (22, 296),
            "pants": (22, 360),
            "accessory_left": (218, 232),
            "accessory_right": (218, 296),
            "shoes": (218, 360),
        }
        for slot, (slot_x, slot_y) in slot_positions.items():
            draw.rectangle(
                (slot_x, slot_y, slot_x + 52, slot_y + 52),
                fill=(255, 203, 139),
                outline=(255, 238, 196),
                width=3,
            )
            icon_color = (113, 79, 59)
            if slot == "hat":
                draw.rectangle((slot_x + 12, slot_y + 19, slot_x + 40, slot_y + 27), outline=icon_color, width=3)
                draw.arc((slot_x + 17, slot_y + 9, slot_x + 36, slot_y + 30), 180, 360, fill=icon_color, width=3)
            elif slot == "shirt":
                draw.polygon([(slot_x+14,slot_y+15),(slot_x+21,slot_y+10),(slot_x+31,slot_y+10),(slot_x+38,slot_y+15),(slot_x+45,slot_y+23),(slot_x+38,slot_y+29),(slot_x+34,slot_y+24),(slot_x+34,slot_y+43),(slot_x+18,slot_y+43),(slot_x+18,slot_y+24),(slot_x+14,slot_y+29),(slot_x+7,slot_y+23)], outline=icon_color)
            elif slot == "pants":
                draw.polygon([(slot_x+13,slot_y+10),(slot_x+39,slot_y+10),(slot_x+36,slot_y+25),(slot_x+35,slot_y+43),(slot_x+27,slot_y+43),(slot_x+25,slot_y+28),(slot_x+22,slot_y+43),(slot_x+14,slot_y+43)], outline=icon_color)
            elif slot.startswith("accessory"):
                draw.ellipse((slot_x+14,slot_y+13,slot_x+38,slot_y+39), outline=icon_color, width=4)
            elif slot == "shoes":
                draw.polygon([(slot_x+8,slot_y+31),(slot_x+19,slot_y+31),(slot_x+22,slot_y+23),(slot_x+28,slot_y+32),(slot_x+43,slot_y+35),(slot_x+43,slot_y+42),(slot_x+8,slot_y+42)], outline=icon_color)
            item = self.equipped[slot]
            if item is not None:
                draw.rectangle(
                    (slot_x + 2, slot_y + 2, slot_x + 50, slot_y + 50),
                    outline=(76, 165, 89),
                    width=3,
                )

        draw.text((304, 240), f"{self.farm_name[:20]}", font=font, fill=(64, 43, 39))
        stat_boxes = (
            (304, 276, f"Balance: {self.coins:,}g"),
            (304, 314, f"Daily earnings: {self.daily_earnings:,}g"),
            (304, 352, f"Day {self.day}  {self.season}  Year {self.year}"),
        )
        for stat_x, stat_y, text in stat_boxes:
            draw.rounded_rectangle(
                (stat_x, stat_y, stat_x + 376, stat_y + 32),
                radius=3,
                fill=(255, 218, 157),
                outline=(170, 116, 72),
                width=2,
            )
            draw.text((stat_x + 9, stat_y + 8), text, font=font, fill=(64, 43, 39))
        draw.text((84, 416), self.character_name[:12], font=font, fill=(64, 43, 39))
        draw.text((162, 416), f"Level {self.level}", font=font, fill=(64, 43, 39))
        trash_x, trash_y = 660, 414
        draw.rectangle((trash_x + 8, trash_y + 12, trash_x + 33, trash_y + 44), fill=(177, 178, 176), outline=(78, 75, 76), width=3)
        draw.rectangle((trash_x + 3, trash_y + 7, trash_x + 38, trash_y + 13), fill=(204, 204, 199), outline=(78, 75, 76), width=2)
        draw.line((trash_x + 15, trash_y + 18, trash_x + 15, trash_y + 38), fill=(82, 80, 78), width=2)
        draw.line((trash_x + 25, trash_y + 18, trash_x + 25, trash_y + 38), fill=(82, 80, 78), width=2)
        draw.text((trash_x - 3, trash_y + 55), "Trash", font=small_font, fill=(64, 43, 39))

        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This inventory belongs to someone else.", ephemeral=True
            )
            return False
        return True
