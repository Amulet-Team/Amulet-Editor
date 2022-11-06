from PySide6.QtWidgets import QMainWindow
from .landing_widget import AmuletLandingWidget


class AmuletLandingWindow(QMainWindow):
    """
    A minimal landing page.
    This should only implement behaviour.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.central_widget = AmuletLandingWidget(self)
        self.setCentralWidget(self.central_widget)
