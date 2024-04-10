# Copyright (C) 2021-2024, Mindee.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://opensource.org/licenses/Apache-2.0> for full license details.

import logging
import platform
from typing import Optional

from PIL import ImageFont

__all__ = ["get_font"]


def get_font(font_family: Optional[str] = None, font_size: int = 13, layout_engine = "basic") -> ImageFont.ImageFont:
    """Resolves a compatible ImageFont for the system

    Args:
    ----
        font_family: the font family to use
        font_size: the size of the font upon rendering

    Returns:
    -------
        the Pillow font
    """
    if layout_engine == "raqm":
        layout_engine = ImageFont.Layout.RAQM
    else:
        layout_engine = ImageFont.Layout.BASIC
    # Font selection
    if font_family is None:
        try:
            font = ImageFont.truetype("FreeMono.ttf" if platform.system() == "Linux" else "Arial.ttf", font_size, layout_engine= layout_engine)
        except OSError:
            font = ImageFont.load_default()
            logging.warning(
                "unable to load recommended font family. Loading default PIL font,"
                "font size issues may be expected."
                "To prevent this, it is recommended to specify the value of 'font_family'."
            )
    else:
        font = ImageFont.truetype(font_family, font_size, layout_engine= layout_engine)

    return font
