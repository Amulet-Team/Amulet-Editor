# from typing import Optional
# from threading import Thread
# import sys
#
# from ._app import AmuletApp
# from ._invoke import invoke
from amulet_editor.models.plugin import Plugin


class AppPlugin(Plugin):
    pass
    # __app: Optional[AmuletApp]
    #
    # def on_init(self):
    #     self.__app = None
    #
    # def on_start(self):
    #     t = Thread(target=self.__main)
    #     t.start()
    #
    # def __main(self):
    #     self.__app = AmuletApp()
    #     sys.exit(self.__app.exec())
    #
    # def on_stop(self):
    #     invoke(self.__app, self.__app.exit)
