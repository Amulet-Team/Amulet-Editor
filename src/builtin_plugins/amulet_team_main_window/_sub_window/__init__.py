from PySide6.QtGui import QCloseEvent

from .sub_window import Ui_AmuletSubWindow


class AmuletSubWindow(Ui_AmuletSubWindow):
    def closeEvent(self, event: QCloseEvent) -> None:
        # The parent keeps this object alive. We need to do this so it can be destroyed
        self.setParent(None)
        self.deleteLater()


sub_windows: list[AmuletSubWindow] = []
