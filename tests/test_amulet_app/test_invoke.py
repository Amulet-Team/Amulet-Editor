import unittest

import shiboken6

from PySide6.QtCore import QTimer, QThread, QObject
from PySide6.QtWidgets import QApplication

from amulet.app.invoke import invoke, enqueue, Promise


class InvokeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if QApplication.instance() is not None:
            raise RuntimeError("QApplication exists")

    @classmethod
    def tearDownClass(cls) -> None:
        if QApplication.instance() is not None:
            raise RuntimeError("QApplication exists")

    def test_invoke_main_from_main(self) -> None:
        app = QApplication()

        try:

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            src_thread: QThread | None = None
            exe_thread_1: QThread | None = None
            i_1: int = 0
            exe_thread_2: QThread | None = None
            i_2: int = 0

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread_1, i_1, exe_thread_2, i_2
                    src_thread = QThread.currentThread()
                    exe_thread_1, i_1 = invoke(func)
                    exe_thread_2, i_2 = invoke(func, app)
                finally:
                    app.quit()

            QTimer.singleShot(0, test_invoke)

            app.exec()

            self.assertEqual(app.thread(), src_thread)
            self.assertEqual(app.thread(), exe_thread_1)
            self.assertEqual(1, i_1)
            self.assertEqual(app.thread(), exe_thread_2)
            self.assertEqual(1, i_2)
        finally:
            shiboken6.delete(app)

    def test_invoke_main_from_thread(self) -> None:
        app = QApplication()

        try:

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            src_thread: QThread | None = None
            t = QThread()
            o = QObject()
            o.moveToThread(t)
            exe_thread_1: QThread | None = None
            i_1: int = 0
            exe_thread_2: QThread | None = None
            i_2: int = 0

            def quit() -> None:
                t.quit()
                app.quit()

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread_1, i_1, exe_thread_2, i_2
                    src_thread = QThread.currentThread()
                    exe_thread_1, i_1 = invoke(func)
                    exe_thread_2, i_2 = invoke(func, app)
                finally:
                    enqueue(quit, app)

            t.start()

            enqueue(test_invoke, o)

            app.exec()

            self.assertEqual(t, src_thread)
            self.assertEqual(app.thread(), exe_thread_1)
            self.assertEqual(1, i_1)
            self.assertEqual(app.thread(), exe_thread_2)
            self.assertEqual(1, i_2)
        finally:
            shiboken6.delete(app)

    def test_invoke_thread_from_main(self) -> None:
        app = QApplication()

        try:

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            src_thread: QThread | None = None
            t = QThread()
            o = QObject()
            o.moveToThread(t)
            exe_thread: QThread | None = None
            i: int = 0

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread, i
                    src_thread = QThread.currentThread()
                    exe_thread, i = invoke(func, o)
                finally:
                    t.quit()
                    app.quit()

            t.start()
            QTimer.singleShot(0, test_invoke)

            app.exec()

            self.assertEqual(app.thread(), src_thread)
            self.assertEqual(t, exe_thread)
            self.assertEqual(1, i)
        finally:
            shiboken6.delete(app)

    def test_invoke_thread_from_thread(self) -> None:
        app = QApplication()

        try:

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            src_thread: QThread | None = None
            t1 = QThread()
            o1 = QObject()
            o1.moveToThread(t1)
            t2 = QThread()
            o2 = QObject()
            o2.moveToThread(t2)
            exe_thread: QThread | None = None
            i: int = 0

            def quit() -> None:
                t1.quit()
                t2.quit()
                app.quit()

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread, i
                    src_thread = QThread.currentThread()
                    exe_thread, i = invoke(func, o1)
                finally:
                    enqueue(quit, app)

            t1.start()
            t2.start()

            enqueue(test_invoke, o2)

            app.exec()

            self.assertEqual(t2, src_thread)
            self.assertEqual(t1, exe_thread)
            self.assertEqual(1, i)
        finally:
            shiboken6.delete(app)


if __name__ == "__main__":
    unittest.main()
