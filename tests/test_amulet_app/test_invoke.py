import unittest

import shiboken6

from PySide6.QtCore import QTimer, QThread, QObject
from PySide6.QtWidgets import QApplication

from amulet.app.invoke import invoke, enqueue


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
            fail = False
            src_thread: QThread | None = None
            exe_thread_1: QThread | None = None
            i_1: int = 0
            exe_thread_2: QThread | None = None
            i_2: int = 0

            def quit_app() -> None:
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread_1, i_1, exe_thread_2, i_2
                    src_thread = QThread.currentThread()
                    exe_thread_1, i_1 = invoke(func)
                    exe_thread_2, i_2 = invoke(func, app)
                finally:
                    quit_app()

            QTimer.singleShot(0, app, test_invoke)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
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
            fail = False
            src_thread: QThread | None = None
            t = QThread()
            o = QObject()
            o.moveToThread(t)
            exe_thread_1: QThread | None = None
            i_1: int = 0
            exe_thread_2: QThread | None = None
            i_2: int = 0

            def quit_app() -> None:
                t.quit()
                t.wait()
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread_1, i_1, exe_thread_2, i_2
                    src_thread = QThread.currentThread()
                    exe_thread_1, i_1 = invoke(func)
                    exe_thread_2, i_2 = invoke(func, app)
                finally:
                    QTimer.singleShot(0, app, quit_app)

            t.start()

            QTimer.singleShot(0, o, test_invoke)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
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
            fail = False
            src_thread: QThread | None = None
            t = QThread()
            o = QObject()
            o.moveToThread(t)
            exe_thread: QThread | None = None
            i: int = 0

            def quit_app() -> None:
                t.quit()
                t.wait()
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread, i
                    src_thread = QThread.currentThread()
                    exe_thread, i = invoke(func, o)
                finally:
                    quit_app()

            t.start()
            QTimer.singleShot(0, app, test_invoke)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
            self.assertEqual(app.thread(), src_thread)
            self.assertEqual(t, exe_thread)
            self.assertEqual(1, i)
        finally:
            shiboken6.delete(app)

    def test_invoke_thread_from_thread(self) -> None:
        app = QApplication()

        try:
            fail = False
            src_thread: QThread | None = None
            t1 = QThread()
            o1 = QObject()
            o1.moveToThread(t1)
            t2 = QThread()
            o2 = QObject()
            o2.moveToThread(t2)
            exe_thread: QThread | None = None
            i: int = 0

            def quit_app() -> None:
                t1.quit()
                t2.quit()
                t1.wait()
                t2.wait()
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> tuple[QThread, int]:
                return QThread.currentThread(), 1

            def test_invoke() -> None:
                try:
                    nonlocal src_thread, exe_thread, i
                    src_thread = QThread.currentThread()
                    exe_thread, i = invoke(func, o1)
                finally:
                    QTimer.singleShot(0, app, quit_app)

            t1.start()
            t2.start()

            QTimer.singleShot(0, o2, test_invoke)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
            self.assertEqual(t2, src_thread)
            self.assertEqual(t1, exe_thread)
            self.assertEqual(1, i)
        finally:
            shiboken6.delete(app)

    def test_enqueue_main_from_main(self) -> None:
        app = QApplication()

        try:
            fail = False
            results: list[tuple[QThread, int]] = []
            src_thread: QThread | None = None

            def quit_app() -> None:
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> None:
                results.append((QThread.currentThread(), len(results)))
                if len(results) == 2:
                    QTimer.singleShot(0, app, quit_app)

            def test_enqueue() -> None:
                nonlocal src_thread
                src_thread = QThread.currentThread()
                enqueue(func)
                enqueue(func, app)

            enqueue(test_enqueue)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
            self.assertEqual(app.thread(), src_thread)
            self.assertEqual(
                [
                    (app.thread(), 0),
                    (app.thread(), 1),
                ],
                results,
            )

        finally:
            shiboken6.delete(app)

    def test_enqueue_main_from_thread(self) -> None:
        app = QApplication()

        try:
            fail = False
            results: list[tuple[QThread, int]] = []
            src_thread: QThread | None = None
            thread_2 = QThread()
            o2 = QObject()
            o2.moveToThread(thread_2)

            def quit_app() -> None:
                thread_2.quit()
                thread_2.wait()
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> None:
                results.append((QThread.currentThread(), len(results)))
                if len(results) == 2:
                    QTimer.singleShot(0, app, quit_app)

            def test_enqueue() -> None:
                nonlocal src_thread
                src_thread = QThread.currentThread()
                enqueue(func)
                enqueue(func, app)

            thread_2.start()

            enqueue(test_enqueue, o2)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
            self.assertEqual(thread_2, src_thread)
            self.assertEqual(
                [
                    (app.thread(), 0),
                    (app.thread(), 1),
                ],
                results,
            )

        finally:
            shiboken6.delete(app)

    def test_enqueue_thread_from_main(self) -> None:
        app = QApplication()

        try:
            fail = False
            results: list[tuple[QThread, int]] = []
            src_thread: QThread | None = None
            thread_2 = QThread()
            o2 = QObject()
            o2.moveToThread(thread_2)

            def quit_app() -> None:
                thread_2.quit()
                thread_2.wait()
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> None:
                results.append((QThread.currentThread(), len(results)))
                if len(results) == 2:
                    QTimer.singleShot(0, app, quit_app)

            def test_enqueue() -> None:
                nonlocal src_thread
                src_thread = QThread.currentThread()
                enqueue(func, o2)

            thread_2.start()

            enqueue(test_enqueue)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
            self.assertEqual(app.thread(), src_thread)
            self.assertEqual(
                [(thread_2, 0)],
                results,
            )

        finally:
            shiboken6.delete(app)

    def test_enqueue_thread_from_thread(self) -> None:
        app = QApplication()

        try:
            fail = False
            results: list[tuple[QThread, int]] = []
            src_thread: QThread | None = None
            thread_2 = QThread()
            o2 = QObject()
            o2.moveToThread(thread_2)
            thread_3 = QThread()
            o3 = QObject()
            o3.moveToThread(thread_3)

            def quit_app() -> None:
                thread_2.quit()
                thread_3.quit()
                thread_2.wait()
                thread_3.wait()
                app.quit()

            def quit_app_fail() -> None:
                quit_app()
                nonlocal fail
                fail = True

            def func() -> None:
                results.append((QThread.currentThread(), len(results)))
                if len(results) == 2:
                    QTimer.singleShot(0, app, quit_app)

            def test_enqueue() -> None:
                nonlocal src_thread
                src_thread = QThread.currentThread()
                enqueue(func, o3)

            thread_2.start()
            thread_3.start()

            enqueue(test_enqueue, o2)
            QTimer.singleShot(2000, app, quit_app_fail)

            app.exec()

            self.assertFalse(fail)
            self.assertEqual(thread_2, src_thread)
            self.assertEqual(
                [(thread_3, 0)],
                results,
            )

        finally:
            shiboken6.delete(app)


if __name__ == "__main__":
    unittest.main()
