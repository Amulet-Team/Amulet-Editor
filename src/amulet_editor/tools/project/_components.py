import re

from amulet_editor.application import appearance
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class QCodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = QLineNumberArea(self)
        self.lineNumberArea.setProperty("backgroundColor", "background")
        self.lineNumberArea.setProperty("borderRight", "surface")
        self.lineNumberArea.setProperty("color", "on_background")

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance("9") * (digits + 2)
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect: QRect, dy: int):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0, rect.y(), self.lineNumberArea.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = appearance.theme().primary_variant.get_qcolor()
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event: QPaintEvent):
        painter = QPainter(self.lineNumberArea)

        painter.fillRect(event.rect(), appearance.theme().background.get_qcolor())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1) + " "
                painter.setPen(appearance.theme().on_surface.get_qcolor())
                painter.drawText(
                    0,
                    top,
                    self.lineNumberArea.width(),
                    height,
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            tc = self.textCursor()
            tc.insertText("    ")
        else:
            super().keyPressEvent(event)


class QLineNumberArea(QWidget):
    def __init__(self, editor: QCodeEditor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event: QPaintEvent):
        self.editor.lineNumberAreaPaintEvent(event)


class MCFunctionHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._mappings = {}

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#529955"))
        pattern = r"^\s*#.*$"
        self.add_mapping(pattern, comment_format)

        function_list = [
            "advancement",
            "attribute",
            "ban",
            "ban-ip",
            "banlist",
            "bossbar",
            "clear",
            "clone",
            "data",
            "datapack",
            "debug",
            "defaultgamemode",
            "deop",
            "difficulty",
            "effect",
            "enchant",
            "execute",
            "experience",
            "fill",
            "forceload",
            "function",
            "gamemode",
            "gamerule",
            "give",
            "help",
            "item",
            "kick",
            "kill",
            "list",
            "locate",
            "locatebiome",
            "loot",
            "me",
            "msg",
            "op",
            "pardon",
            "pardon-ip",
            "particle",
            "perf",
            "place",
            "playsound",
            "publish",
            "recipe",
            "reload",
            "save-all",
            "save-off",
            "save-on",
            "say",
            "schedule",
            "scoreboard",
            "seed",
            "setblock",
            "setidletimeout",
            "setworldspawn",
            "spawnpoint",
            "spectate",
            "spreadplayers",
            "stop",
            "stopsound",
            "summon",
            "tag",
            "team",
            "teammsg",
            "teleport",
            "tell",
            "tellraw",
            "time",
            "title",
            "tm",
            "tp",
            "trigger",
            "warden_spawn_tracker",
            "weather",
            "whitelist",
            "worldborder",
            "xp",
        ]
        function_re = "|".join(function_list)
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#c586c0"))
        pattern = r"^(" + function_re + r")\b|(?<=run )\b(" + function_re + r")\b"
        self.add_mapping(pattern, function_format)

    def add_mapping(self, pattern, fmt):
        self._mappings[pattern] = fmt

    def highlightBlock(self, text):
        for pattern, fmt in self._mappings.items():
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._mappings = {}

        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor("#569cd6"))
        pattern = r"([tT]rue|[fF]alse)"
        self.add_mapping(pattern, bool_format)

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f4ab6e"))
        pattern = r"\"(.*?)(?<!\\)\""
        self.add_mapping(pattern, string_format)

        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#9cdcfe"))
        pattern = r"(\".*\")(?=\s*:)"
        self.add_mapping(pattern, key_format)

        string_value_format = QTextCharFormat()
        string_value_format.setForeground(QColor("#f4ab6e"))
        pattern = r"(?<=:\s)([\"\'].*[\"\'])"
        self.add_mapping(pattern, string_value_format)

        number_value_format = QTextCharFormat()
        number_value_format.setForeground(QColor("#a7cea8"))
        pattern = r"(?<=:\s)(-*((\d+[.]\d+)|(\d+)))"
        self.add_mapping(pattern, number_value_format)

    def add_mapping(self, pattern, fmt):
        self._mappings[pattern] = fmt

    def highlightBlock(self, text):
        for pattern, fmt in self._mappings.items():
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)
