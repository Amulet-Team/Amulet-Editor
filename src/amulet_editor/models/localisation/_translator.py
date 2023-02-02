from typing import Optional
import os
from PySide6.QtCore import QTranslator, QLocale, QDir


class ATranslator(QTranslator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._translations: dict[str, str] = {}
        self._path = ""

    def filePath(self) -> str:
        return super().filePath() or self._path

    def isEmpty(self) -> bool:
        return super().isEmpty() and not self._translations

    def load_lang(
        self,
        locale: QLocale,
        filename: str,
        prefix: str = "",
        directory: str = "",
        suffix: str = ".lang",
    ) -> bool:
        self._translations.clear()

        def get_codes():
            for language_ in locale.uiLanguages():
                language_split = language_.split("-")
                for i in range(len(language_split), -1, -1):
                    yield "_".join(language_split[:i])
            yield "en"

        directory = directory or QDir.currentPath()

        for ui_language_name in get_codes():
            for ext in [suffix, ""]:
                path = (
                    directory + os.path.sep + filename + prefix + ui_language_name + ext
                )
                if os.path.isfile(path):
                    with open(path) as lang:
                        for line in lang.readlines():
                            line = line.strip()
                            if not line or line[0] == "#":
                                continue
                            else:
                                line_split = line.split("=", 1)
                                if len(line_split) != 2:
                                    # TODO: error dialog
                                    continue
                                self._translations[line_split[0]] = line_split[1]
                    return True
        return False

    def translate(
        self,
        context: str,
        source_text: str,
        disambiguation: Optional[bytes] = None,
        n: int = -1,
    ) -> str:
        return super().translate(
            context, source_text, disambiguation, n
        ) or self._translations.get(f"{context}.{source_text}", None)
