from amulet_editor.application._app import AmuletApp


def get_app() -> AmuletApp:
    return AmuletApp.instance()
