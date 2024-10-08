#!/usr/bin/env python
#
# Copyright (c) 2014 Matthew Borgerson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""Texture Atlas and Map File Generation Utility Classes"""

import logging
from PIL import Image
import math
from collections.abc import Collection
from amulet_editor.models.generic._promise import Promise

log = logging.getLogger(__name__)

DESCRIPTION = """Packs many smaller images into one larger image, a Texture
Atlas. A companion file (.map), is created that defines where each texture is
mapped in the atlas."""


class AtlasTooSmall(Exception):
    pass


class Packable:
    """A two-dimensional object with position information."""

    def __init__(self, width: int, height: int) -> None:
        self._x = 0
        self._y = 0
        self._width = width
        self._height = height

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, value: int) -> None:
        self._x = value

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, value: int) -> None:
        self._y = value

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def perimeter(self) -> int:
        return 2 * self._width + 2 * self._height


class PackRegion:
    """A region that two-dimensional Packable objects can be packed into."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        """Constructor."""
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._sub1: PackRegion | None = None
        self._sub2: PackRegion | None = None
        self._packable: Packable | None = None

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def packable(self) -> Packable | None:
        return self._packable

    def get_all_packables(self) -> list[Packable]:
        """Returns a list of all Packables in this region and sub-regions."""
        packables = []
        if self._packable is not None:
            packables.append(self._packable)
        if self._sub1 is not None:
            packables.extend(self._sub1.get_all_packables())
        if self._sub2 is not None:
            packables.extend(self._sub2.get_all_packables())
        return packables

    def pack(self, packable: Packable, border: int) -> bool:
        """Pack 2D packable into this region."""
        if not self._packable:
            # Is there room to pack this?
            if (packable.width + border * 2 > self._width) or (
                packable.height + border * 2 > self._height
            ):
                return False

            # Pack
            self._packable = packable

            # Set x, y on Packable
            self._packable.x = self._x + border
            self._packable.y = self._y + border

            # Create sub-regions
            self._sub1 = PackRegion(
                self._x,
                self._y + self._packable.height + border * 2,
                self._packable.width + border * 2,
                self._height - self._packable.height - border * 2,
            )
            self._sub2 = PackRegion(
                self._x + self._packable.width + border * 2,
                self._y,
                self._width - self._packable.width - border * 2,
                self._height,
            )
            return True

        # Pack into sub-region
        assert self._sub1 is not None and self._sub2 is not None
        return self._sub1.pack(packable, border) or self._sub2.pack(packable, border)


class Frame(Packable):
    """An image file that can be packed into a PackRegion."""

    def __init__(self, filename: str) -> None:
        self._filename = filename

        # Determine frame dimensions
        image: Image.Image = Image.open(filename)
        self._image: Image.Image = image.copy()
        image.close()

        width, height = self._image.size

        super(Frame, self).__init__(width, height)

    @property
    def filename(self) -> str:
        return self._filename

    def draw(self, image: Image.Image, border: int) -> None:
        """Draw this frame into another Image."""
        if border:
            image.paste(
                self._image.resize(tuple(s + border * 2 for s in self._image.size)),
                (self.x - border, self.y - border),
            )
        image.paste(self._image, (self.x, self.y))


class Texture:
    """A collection of one or more frames."""

    def __init__(self, name: str, frames: list[Frame]) -> None:
        self._name = name
        self._frames: list[Frame] = frames

    @property
    def name(self) -> str:
        return self._name

    @property
    def frames(self) -> list[Frame]:
        return self._frames


class TextureAtlas(PackRegion):
    """Texture Atlas generator."""

    def __init__(self, width: int, height: int, border: int = 0) -> None:
        super(TextureAtlas, self).__init__(0, 0, width, height)
        self._textures: list[Texture] = []
        self._border = border

    @property
    def textures(self) -> list[Texture]:
        return self._textures

    def pack_texture(self, texture: Texture) -> None:
        """Pack a Texture into this atlas."""
        self._textures.append(texture)
        for frame in texture.frames:
            if not self.pack(frame, self._border):
                raise AtlasTooSmall("Failed to pack frame %s" % frame.filename)

    def to_dict(self) -> dict[str, tuple[float, float, float, float]]:
        return {
            tex.name: (
                tex.frames[0].x / self.width,
                tex.frames[0].y / self.height,
                (tex.frames[0].x + tex.frames[0].width) / self.width,
                (tex.frames[0].y + min(tex.frames[0].height, tex.frames[0].width))
                / self.height,
            )
            for tex in self.textures
        }

    def generate(self, mode: str) -> Image.Image:
        """Generates the final texture atlas."""
        out = Image.new(mode, (self.width, self.height))
        for t in self._textures:
            for f in t.frames:
                f.draw(out, self._border)
        return out

    def write(self, filename: str, mode: str) -> None:
        """Generates and saves the final texture atlas."""
        out = self.generate(mode)
        out.save(filename)


def create_atlas(
    texture_tuple: Collection[str],
) -> Promise[tuple[Image.Image, dict[str, tuple[float, float, float, float]]]]:
    def func(
        promise_data: Promise.Data,
    ) -> tuple[Image.Image, dict[str, tuple[float, float, float, float]]]:
        log.info("Creating texture atlas")
        # Parse texture names
        textures = []
        for texture_index, texture_path in enumerate(texture_tuple):
            if not texture_index % 100:
                promise_data.progress_change.emit(
                    0.5 * texture_index / (len(texture_tuple))
                )

            # Build frame objects
            frames = [Frame(texture_path)]

            # Add frames to texture object list
            textures.append(Texture(texture_path, frames))

        # Sort textures by perimeter size in non-increasing order
        textures = sorted(textures, key=lambda i: i.frames[0].perimeter, reverse=True)

        height = 0
        width = 0
        pixels = 0
        for t in textures:
            for f in t.frames:
                height = max(f.height, height)
                width = max(f.width, width)
                pixels += f.height * f.width

        size = max(height, width, 1 << (math.ceil(pixels**0.5) - 1).bit_length())

        while True:
            try:
                # Create the atlas and pack textures in
                log.info(f"Trying to pack textures into image of size {size}x{size}")
                atlas = TextureAtlas(size, size)

                for texture_index, texture in enumerate(textures):
                    if not texture_index % 30:
                        promise_data.progress_change.emit(
                            0.5 + 0.5 * texture_index / len(textures)
                        )
                    atlas.pack_texture(texture)
                break
            except AtlasTooSmall:
                log.info(f"Image was too small. Trying with a larger area")
                size *= 2

        log.info(f"Successfully packed textures into an image of size {size}x{size}")

        texture_atlas = atlas.generate("RGBA")

        texture_bounds = atlas.to_dict()
        texture_bounds = {
            texture_path: texture_bounds[texture_path] for texture_path in texture_tuple
        }

        log.info("Finished creating texture atlas")
        return texture_atlas, texture_bounds

    return Promise(func)
