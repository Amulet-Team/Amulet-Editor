from amulet_editor.data._localisation import set_locale, locale_changed  # noqa
from amulet_editor.models.plugin import PluginV1


def load_plugin():
    # TODO: load locale this from a config file
    pass


plugin = PluginV1(load_plugin)
