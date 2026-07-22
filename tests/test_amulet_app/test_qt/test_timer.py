"""
This is to test my understanding of QTimer.singleShot.
It always runs in queued mode.
If no context is specified, the function is invoked in the current thread.
"""

import unittest

import shiboken6

from PySide6.QtCore import QTimer, QObject
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication


class TimerTestCase(unittest.TestCase):
    def test_single_shot(self) -> None:
        for i in range(40):
            with self.subTest(i=i + 1):
                app = QApplication()

                try:
                    thread_2 = QThread()
                    o2 = QObject()
                    o2.moveToThread(thread_2)
                    thread_3 = QThread()
                    o3 = QObject()
                    o3.moveToThread(thread_3)

                    result_1a: QThread | None = None
                    result_1b: QThread | None = None
                    result_1c: QThread | None = None
                    result_1d: QThread | None = None
                    result_1e: QThread | None = None
                    result_2a: QThread | None = None
                    result_2b: QThread | None = None
                    result_2c: QThread | None = None
                    result_2d: QThread | None = None
                    result_2e: QThread | None = None
                    result_3a: QThread | None = None
                    result_3b: QThread | None = None
                    result_3c: QThread | None = None
                    result_3d: QThread | None = None
                    result_3e: QThread | None = None

                    def func_1a() -> None:
                        nonlocal result_1a
                        result_1a = QThread.currentThread()
                        QTimer.singleShot(0, func_1b)

                    def func_1b() -> None:
                        nonlocal result_1b
                        result_1b = QThread.currentThread()
                        QTimer.singleShot(0, app, func_1c)

                    def func_1c() -> None:
                        nonlocal result_1c
                        result_1c = QThread.currentThread()
                        QTimer.singleShot(10, func_1d)

                    def func_1d() -> None:
                        nonlocal result_1d
                        result_1d = QThread.currentThread()
                        QTimer.singleShot(10, app, func_1e)

                    def func_1e() -> None:
                        nonlocal result_1e
                        result_1e = QThread.currentThread()
                        QTimer.singleShot(0, o2, func_2a)

                    def func_2a() -> None:
                        nonlocal result_2a
                        result_2a = QThread.currentThread()
                        QTimer.singleShot(0, func_2b)

                    def func_2b() -> None:
                        nonlocal result_2b
                        result_2b = QThread.currentThread()
                        QTimer.singleShot(0, o2, func_2c)

                    def func_2c() -> None:
                        nonlocal result_2c
                        result_2c = QThread.currentThread()
                        QTimer.singleShot(10, func_2d)

                    def func_2d() -> None:
                        nonlocal result_2d
                        result_2d = QThread.currentThread()
                        QTimer.singleShot(10, o2, func_2e)

                    def func_2e() -> None:
                        nonlocal result_2e
                        result_2e = QThread.currentThread()
                        QTimer.singleShot(0, o3, func_3a)

                    def func_3a() -> None:
                        nonlocal result_3a
                        result_3a = QThread.currentThread()
                        QTimer.singleShot(0, func_3b)

                    def func_3b() -> None:
                        nonlocal result_3b
                        result_3b = QThread.currentThread()
                        QTimer.singleShot(0, o3, func_3c)

                    def func_3c() -> None:
                        nonlocal result_3c
                        result_3c = QThread.currentThread()
                        QTimer.singleShot(10, func_3d)

                    def func_3d() -> None:
                        nonlocal result_3d
                        result_3d = QThread.currentThread()
                        QTimer.singleShot(10, o3, func_3e)

                    def func_3e() -> None:
                        nonlocal result_3e
                        result_3e = QThread.currentThread()
                        QTimer.singleShot(0, app, quit_app)

                    def quit_app() -> None:
                        thread_2.quit()
                        thread_3.quit()
                        thread_2.wait()
                        thread_3.wait()
                        app.quit()

                    thread_2.start()
                    thread_3.start()

                    QTimer.singleShot(0, func_1a)
                    QTimer.singleShot(5000, quit_app)

                    app.exec()

                    self.assertEqual(app.thread(), result_1a)
                    self.assertEqual(app.thread(), result_1b)
                    self.assertEqual(app.thread(), result_1c)
                    self.assertEqual(app.thread(), result_1d)
                    self.assertEqual(app.thread(), result_1e)
                    self.assertEqual(thread_2, result_2a)
                    self.assertEqual(thread_2, result_2b)
                    self.assertEqual(thread_2, result_2c)
                    self.assertEqual(thread_2, result_2d)
                    self.assertEqual(thread_2, result_2e)
                    self.assertEqual(thread_3, result_3a)
                    self.assertEqual(thread_3, result_3b)
                    self.assertEqual(thread_3, result_3c)
                    self.assertEqual(thread_3, result_3d)
                    self.assertEqual(thread_3, result_3e)
                finally:
                    shiboken6.delete(app)

    def test_single_shot_method(self) -> None:
        app = QApplication()

        try:
            thread_2 = QThread()

            def quit_app() -> None:
                thread_2.quit()
                thread_2.wait()
                app.quit()

            result_1: QThread | None = None
            result_2: QThread | None = None

            class Object(QObject):
                def func_1(self) -> None:
                    nonlocal result_1
                    result_1 = QThread.currentThread()
                    QTimer.singleShot(0, o2, o2.func_2)

                def func_2(self) -> None:
                    nonlocal result_2
                    result_2 = QThread.currentThread()
                    QTimer.singleShot(0, app, quit_app)

            o2 = Object()
            o2.moveToThread(thread_2)

            thread_2.start()

            QTimer.singleShot(0, o2.func_1)
            QTimer.singleShot(5000, quit_app)

            app.exec()

            self.assertEqual(app.thread(), result_1)
            self.assertEqual(thread_2, result_2)
        finally:
            shiboken6.delete(app)


if __name__ == "__main__":
    unittest.main()
