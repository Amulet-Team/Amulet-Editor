import unittest
import sys
import os

from amulet.app.path._plugin import first_party_plugin_directory


class TestQtLink(unittest.TestCase):
    def setUp(self) -> None:
        sys.path.append(first_party_plugin_directory())

    def tearDown(self) -> None:
        sys.path.remove(first_party_plugin_directory())

    def test_qt_link(self) -> None:
        from PySide6 import __version__ as qt_version
        from plugin.amulet.editor.widget._view_3d._view_3d import (
            _get_qt_version,
        )

        self.assertEqual(qt_version, _get_qt_version())


if __name__ == "__main__":
    unittest.main()
