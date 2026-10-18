import io
import random

import discord
from PIL import Image, ImageDraw, ImageFont


FISH_VERSION_COUNT = 10


def version_settings(version: int) -> tuple[int, int]:
    level = max(1, min(FISH_VERSION_COUNT, version))
    bar_height = 110 - (level - 1) * 8
    fish_drift = 6 + (level - 1) * 2
    return bar_height, fish_drift


class FishingControlButton(discord.ui.Button):
    def __init__(self, label: str, direction: int) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=0)
        self.direction = direction

    async def callback(self, interaction: discord.Interaction) -> None:
        view: FishingGameView = self.view
        view.advance(self.direction)
        image = discord.File(view.render(), filename="fishing_test.png")
        if view.result is not None:
            view.stop()
            await interaction.response.edit_message(
                content=view.status,
                attachments=[image],
                view=None,
            )
            return
        await interaction.response.edit_message(
            content=view.status,
            attachments=[image],
            view=view,
        )


class FishingGameView(discord.ui.View):
    width = 166
    height = 332
    track_top = 24
    track_bottom = 278
    track_left = 61
    track_right = 136
    progress_left = 24
    progress_right = 39

    def __init__(self, owner_id: int, version: int = 1) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.version = max(1, min(FISH_VERSION_COUNT, version))
        self.version_name = f"fish_{self.version}"
        self.bar_height, self.fish_drift = version_settings(self.version)
        self.bar_center = (self.track_top + self.track_bottom) // 2
        self.fish_x = (self.track_left + self.track_right) // 2
        self.fish_center = random.randint(
            self.track_top + 12, self.track_bottom - 12
        )
        self.progress = 0
        self.turns = 0
        self.result: str | None = None
        self.add_item(FishingControlButton("▲ Up", -1))
        self.add_item(FishingControlButton("▼ Down", 1))

    @property
    def status(self) -> str:
        if self.result is not None:
            return f"Fishing test | {self.version_name} | {self.result}"
        return f"Fishing test | {self.version_name} | Catch progress: {self.progress}%"

    def advance(self, direction: int) -> None:
        half_bar = self.bar_height // 2
        self.bar_center = max(
            self.track_top + half_bar,
            min(self.track_bottom - half_bar, self.bar_center + direction * 20),
        )
        self.fish_center = max(
            self.track_top + 12,
            min(
                self.track_bottom - 12,
                self.fish_center + random.randint(-self.fish_drift, self.fish_drift),
            ),
        )
        self.turns += 1
        if abs(self.fish_center - self.bar_center) <= half_bar - 8:
            self.progress = min(100, self.progress + 12)
        else:
            self.progress = max(0, self.progress - 8)
        if self.progress >= 100:
            self.result = "You caught the fish! This was only a test."
        elif self.turns >= 35:
            self.result = "The fish got away. This was only a test."

    def render(self) -> io.BytesIO:
        image = Image.new("RGBA", (self.width, self.height), (27, 37, 55, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (10, 10, 153, 305),
            fill=(56, 69, 91),
            outline=(164, 135, 91),
            width=3,
        )
        draw.rectangle(
            (self.track_left, self.track_top, self.track_right, self.track_bottom),
            fill=(28, 49, 72),
            outline=(218, 191, 128),
            width=3,
        )
        bar_top = self.bar_center - self.bar_height // 2
        bar_bottom = self.bar_center + self.bar_height // 2
        draw.rectangle(
            (self.track_left + 5, bar_top, self.track_right - 5, bar_bottom),
            fill=(73, 169, 93),
            outline=(218, 191, 128),
            width=3,
        )
        fish_y = self.fish_center
        draw.polygon(
            [
                (self.fish_x - 18, fish_y),
                (self.fish_x - 6, fish_y - 13),
                (self.fish_x + 18, fish_y),
                (self.fish_x - 6, fish_y + 13),
            ],
            fill=(255, 220, 103),
            outline=(255, 245, 190),
        )
        draw.rectangle(
            (self.progress_left, self.track_top, self.progress_right, self.track_bottom),
            fill=(28, 49, 72),
            outline=(218, 191, 128),
            width=2,
        )
        progress_height = round(
            (self.track_bottom - self.track_top) * self.progress / 100
        )
        if progress_height:
            draw.rectangle(
                (
                    self.progress_left + 3,
                    self.track_bottom - progress_height,
                    self.progress_right - 3,
                    self.track_bottom - 2,
                ),
                fill=(95, 207, 112),
            )
        font = ImageFont.load_default(size=14)
        draw.text(
            (13, 286),
            f"Catch {self.progress}%",
            font=font,
            fill=(255, 255, 255),
        )
        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This fishing test belongs to someone else.", ephemeral=True
            )
            return False
        return True


class FishingVersionButton(discord.ui.Button):
    def __init__(self, owner_id: int, version: int) -> None:
        super().__init__(
            label=f"fish_{version}",
            style=discord.ButtonStyle.secondary,
            row=(version - 1) // 2,
        )
        self.owner_id = owner_id
        self.version = version

    async def callback(self, interaction: discord.Interaction) -> None:
        game = FishingGameView(self.owner_id, self.version)
        await interaction.response.edit_message(
            content=game.status,
            attachments=[discord.File(game.render(), filename="fishing_test.png")],
            view=game,
        )


class FishingVersionSelectView(discord.ui.View):
    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=180)
        self.owner_id = owner_id
        for version in range(1, FISH_VERSION_COUNT + 1):
            self.add_item(FishingVersionButton(owner_id, version))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This fishing test belongs to someone else.", ephemeral=True
            )
            return False
        return True
