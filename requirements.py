import os
from packaging.version import Version

AMULET_COMPILER_TARGET_REQUIREMENT = "==2.0"
AMULET_COMPILER_VERSION_REQUIREMENT = "==3.0.0"


def get_specifier_set(version_str: str) -> str:
    """
    version_str: The PEP 440 version number of the library.
    """
    version = Version(version_str)
    if version.epoch != 0 or version.is_devrelease or version.is_postrelease:
        raise RuntimeError(f"Unsupported version format. {version_str}")

    return f"~={version.major}.{version.minor}.{version.micro}.0{''.join(map(str, version.pre or ()))}"


if os.environ.get("AMULET_FREEZE_COMPILER", None):
    import get_compiler

    AMULET_COMPILER_VERSION_REQUIREMENT = get_compiler.main()


def get_build_dependencies() -> list:
    return [
        f"amulet-compiler-version{AMULET_COMPILER_VERSION_REQUIREMENT}",
    ] * (not os.environ.get("AMULET_SKIP_COMPILE", None))


def get_runtime_dependencies() -> list[str]:
    return [
        f"amulet-compiler-target{AMULET_COMPILER_TARGET_REQUIREMENT}",
        f"amulet-compiler-version{AMULET_COMPILER_VERSION_REQUIREMENT}",
    ]
