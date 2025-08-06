import unittest


class TestPlugin(unittest.TestCase):
    def test_plugin_import(self) -> None:
        with self.assertRaises(ImportError):
            import builtin_plugins


if __name__ == "__main__":
    unittest.main()
