from pathlib import Path

import discord


ITEMS_PER_PAGE = 10
class InventoryPageButton(discord.ui.Button):
    def __init__(self, label: str, direction: int, row: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        view: InventoryView = self.view
        view.page = max(0, min(view.page_count - 1, view.page + self.direction))
        view.update_buttons()
        embed, portrait_file = view.render_page()
        await interaction.response.edit_message(
            embed=embed,
            attachments=[portrait_file] if portrait_file else [],
            view=view,
        )


class InventoryView(discord.ui.View):
    def __init__(
        self,
        owner_id: int,
        display_name: str,
        avatar_url: str,
        portrait_path: Path,
    ) -> None:
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.portrait_path = portrait_path
        self.items: list[tuple[str, int, str, str]] = []
        self.page = 0
        self.page_count = max(1, (len(self.items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self.previous_button = InventoryPageButton("Previous", -1, row=0)
        self.next_button = InventoryPageButton("Next", 1, row=0)
        self.add_item(self.previous_button)
        self.add_item(self.next_button)
        self.update_buttons()

    def update_buttons(self) -> None:
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.page_count - 1

    def render_page(self) -> tuple[discord.Embed, discord.File | None]:
        start = self.page * ITEMS_PER_PAGE
        page_items = self.items[start : start + ITEMS_PER_PAGE]
        lines = (
            [
                f"{emoji} **{quantity}× {name}** — {description}"
                for name, quantity, description, emoji in page_items
            ]
            if page_items
            else ["Your inventory is empty."]
        )
        embed = discord.Embed(
            description="\n".join(lines),
            color=discord.Color.from_rgb(104, 147, 91),
        )
        embed.set_author(name="Inventory", icon_url=self.avatar_url)
        portrait_file = None
        if self.portrait_path.is_file():
            portrait_file = discord.File(self.portrait_path, filename="profile.png")
            embed.set_author(name="Inventory", icon_url="attachment://profile.png")
        footer = f"{self.display_name} • Page {self.page + 1}/{self.page_count} • "
        footer += (
            f"Showing items {start + 1}–{start + len(page_items)} of {len(self.items)}"
            if page_items
            else "No items"
        )
        embed.set_footer(text=footer)
        return embed, portrait_file

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This inventory belongs to someone else.", ephemeral=True
            )
            return False
        return True
