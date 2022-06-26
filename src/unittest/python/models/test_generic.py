import unittest

from amulet_editor.models.generic import Signal


class TestSignal(unittest.TestCase):
    def test_connect_none(self):
        """Connect one slot to signal and ensure it exists"""

        def test_slot() -> None:
            pass

        signal = Signal(None)
        signal.connect(test_slot)

        self.assertIn(test_slot, signal._slots)
        self.assertEqual(len(signal._slots), 1)

    def test_emit_none(self):
        """Emit signal twice and ensure both events occur"""
        self.emit_count = 0

        def test_slot() -> None:
            self.emit_count += 1

        signal = Signal(None)
        signal.connect(test_slot)

        signal.emit()
        self.assertEqual(self.emit_count, 1)
        signal.emit()
        self.assertEqual(self.emit_count, 2)

    def test_emit_raise(self):
        """Attempt to pass invalid emit types"""

        class TestClass:
            def __init__(self) -> None:
                pass

        signal = Signal(str)

        with self.assertRaises(TypeError):
            signal.emit(1)
        with self.assertRaises(TypeError):
            signal.emit(TestClass)

    def test_emit_class(self):
        """Emit class and subclass and ensure both are valid"""
        self.emit_count = 0

        class TestClass:
            def __init__(self) -> None:
                pass

        class TestSubclass(TestClass):
            def __init__(self) -> None:
                pass

        def test_slot(cls: TestClass) -> None:
            self.assertIsInstance(cls, TestClass)
            self.emit_count += 1

        signal = Signal(TestClass)

        signal.connect(test_slot)

        signal.emit(TestClass())
        self.assertEqual(self.emit_count, 1)
        signal.emit(TestSubclass())
        self.assertEqual(self.emit_count, 2)


if __name__ == "__main__":
    unittest.main()
