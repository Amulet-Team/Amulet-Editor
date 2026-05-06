import unittest


class TestQtLink(unittest.TestCase):
    def test_qt_link(self) -> None:
        from PySide6 import __version__ as qt_version
        from plugin.amulet.editor.widget._view_3d._view_3d import (
            _get_qt_version,
        )

        self.assertEqual(qt_version, _get_qt_version())


if __name__ == "__main__":
    unittest.main()
