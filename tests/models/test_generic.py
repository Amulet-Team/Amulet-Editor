import unittest

from amulet_editor.models.generic import Observer


class TestObserver(unittest.TestCase):
    def test_connect_none(self):
        """Connect one callback to observer and ensure it exists"""

        def test_callback():
            pass

        observer = Observer(None)
        observer.connect(test_callback)

        self.assertIn(test_callback, observer._callbacks)
        self.assertEqual(len(observer._callbacks), 1)

    def test_emit_none(self):
        """Emit observer twice and ensure both events occur"""
        self.emit_count = 0

        def test_callback():
            self.emit_count += 1

        observer = Observer(None)
        observer.connect(test_callback)

        observer.emit()
        self.assertEqual(self.emit_count, 1)
        observer.emit()
        self.assertEqual(self.emit_count, 2)

    def test_emit_raise(self):
        """Attempt to pass invalid emit types"""

        class TestClass:
            def __init__(self):
                pass

        observer = Observer(str)

        with self.assertRaises(TypeError):
            observer.emit(1)
        with self.assertRaises(TypeError):
            observer.emit(TestClass)

    def test_emit_class(self):
        """Emit class and subclass and ensure both are valid"""
        self.emit_count = 0

        class TestClass:
            def __init__(self):
                pass

        class TestSubclass(TestClass):
            def __init__(self):
                pass

        def test_callback(cls: TestClass):
            self.assertIsInstance(cls, TestClass)
            self.emit_count += 1

        observer = Observer(TestClass)

        observer.connect(test_callback)

        observer.emit(TestClass())
        self.assertEqual(self.emit_count, 1)
        observer.emit(TestSubclass())
        self.assertEqual(self.emit_count, 2)


if __name__ == "__main__":
    unittest.main()
