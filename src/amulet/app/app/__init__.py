"""
app_created is a Qt Signal emitted when the app is created.
app_created.connect(func) will call func after the app is created.
app_created.emit() must be called by the code that creates the app.
"""

from ._app import app_created
