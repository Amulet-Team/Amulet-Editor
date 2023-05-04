from copy import deepcopy

from amulet_editor.data.packages._cache import enabled_tools, installed_packages
from amulet_editor.models.package import AmuletPackage, AmuletTool


def install_builtins():
    pass


def list_tools():
    return enabled_tools


def enable_tool(tool: AmuletTool):
    if tool not in enabled_tools:
        enabled_tools.append(tool)


def disable_tool(tool: AmuletTool):
    if tool in enabled_tools:
        enabled_tools.remove(tool)


def list_packages():
    return installed_packages


def install_package(package: AmuletPackage):
    if package not in installed_packages:
        installed_packages.append(package)


def uninstall_package(package: AmuletPackage):
    if package in installed_packages:
        installed_packages.remove(package)
