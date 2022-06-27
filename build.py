from os.path import dirname, exists

import fbs.cmdline
from fbs import SETTINGS, activate_profile, path
from fbs.builtin_commands import clean, freeze, installer, sign, sign_installer
from fbs.builtin_commands._util import (
    is_valid_version,
    prompt_for_value,
    require_existing_project,
    update_json,
)
from fbs.cmdline import command
from fbs_runtime import FbsError
from fbs_runtime.platform import is_arch_linux, is_fedora, is_windows


@command
def release(version=None):
    """
    Bump version and run clean,freeze,...
    """
    require_existing_project()
    if version is None:
        curr_version = SETTINGS["version"]
        next_version = _get_next_version(curr_version)
        release_version = prompt_for_value("Release version", default=next_version)
    elif version == "current":
        release_version = SETTINGS["version"]
    else:
        release_version = version
    if not is_valid_version(release_version):
        if not is_valid_version(version):
            raise FbsError(
                "The release version of your app is invalid. It should be "
                'three\nnumbers separated by dots, such as "1.2.3". '
                'You have: "%s".' % release_version
            )
    activate_profile("release")
    SETTINGS["version"] = release_version

    try:
        clean()
        freeze()
        if is_windows() and _has_windows_codesigning_certificate():
            sign()
        installer()
        if (
            (is_windows() and _has_windows_codesigning_certificate())
            or is_arch_linux()
            or is_fedora()
        ):
            sign_installer()
    finally:
        pass

    base_json = "src/build/settings/base.json"
    update_json(path(base_json), {"version": release_version})


def _has_windows_codesigning_certificate():
    assert is_windows()
    from fbs.sign.windows import _CERTIFICATE_PATH

    return exists(path(_CERTIFICATE_PATH))


def _get_next_version(version):
    version_parts = version.split(".")
    next_patch = str(int(version_parts[-1]) + 1)
    return ".".join(version_parts[:-1]) + "." + next_patch


if __name__ == "__main__":
    project_dir = dirname(__file__)
    fbs.cmdline.main(project_dir)
