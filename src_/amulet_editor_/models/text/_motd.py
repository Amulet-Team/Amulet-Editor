from typing import Optional


class Motd:
    def __init__(self, text: str):
        self.__text = text
        self.__plain_text = "".join(
            val[1:] if index > 0 else val
            for index, val in enumerate(text.split("\u00A7"))
        )

    def __str__(self):
        return self.__plain_text

    def __repr__(self):
        return f"Motd({self.__text})"

    def is_formatted(self):
        return self.__text != self.__plain_text

    def get_text(self):
        return self.__text

    def get_plain_text(self):
        return self.__plain_text

    def get_html(
        self, font_size: Optional[int] = None, font_weight: Optional[int] = None
    ):
        """
        Convert Motd into formatted html by parsing formatting codes such as §a

        font_size
         Sets the absolute size of the text in points.
        font_weight
         Sets how thick or thin characters in text should be displayed.
        """

        motd_split = [
            sect
            for section in [
                ("\u00A7" + val[:1], val[1:]) if index > 0 else (val,)
                for index, val in enumerate(self.__text.split("\u00A7"))
                if not val == ""
            ]
            for sect in section
        ]

        color_codes = {
            "0": "#000000",
            "1": "#0000AA",
            "2": "#00AA00",
            "3": "#00AAAA",
            "4": "#AA0000",
            "5": "#AA00AA",
            "6": "#FFAA00",
            "7": "#AAAAAA",
            "8": "#555555",
            "9": "#5555FF",
            "a": "#55FF55",
            "b": "#55FFFF",
            "c": "#FF5555",
            "d": "#FF55FF",
            "e": "#FFFF55",
            "f": "#FFFFFF",
        }

        style_definitions = {
            "font-size": font_size,
            "font-weight": font_weight,
            "font-style": None,
            "text-decoration": None,
            "color": "#FFFFFF",
        }

        rtf = ""
        for item in motd_split:
            if "\u00A7" not in item:
                style = (
                    ""
                    if not any(value is None for value in style_definitions.values())
                    else ' style="{}"'.format(
                        " ".join(
                            [
                                f"{definition}:{value};"
                                for definition, value in style_definitions.items()
                                if value is not None
                            ]
                        )
                    )
                )
                rtf += f"<span{style}>{item}</span>"
            elif item[1] == "l":
                style_definitions["font-weight"] = 600
            elif item[1] == "o":
                style_definitions["font-style"] = "italic"
            elif item[1] == "n":
                style_definitions["text-decoration"] = "underline"
            elif item[1] == "r":
                style_definitions = {
                    "font-size": font_size,
                    "font-weight": font_weight,
                    "font-style": None,
                    "text-decoration": None,
                    "color": "#FFFFFF",
                }
            elif item[1] in color_codes:
                style_definitions["color"] = color_codes[item[1]]

        return rtf
