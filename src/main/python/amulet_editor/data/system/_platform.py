import csv
import platform


def _platform_name():
    systems = {"Darwin": "mac", "Linux": "linux", "Windows": "windows"}

    try:
        return systems[platform.system()]
    except KeyError:
        raise OSError("{} OS is not supported".format(platform.system()))


def _linux_release():
    if _platform_name() == "linux":
        os_release = {}

        with open("/etc/os-release") as f:
            reader = csv.reader(f, delimiter="=")
            for row in reader:
                if row:
                    os_release[row[0]] = row[1]

        if os_release["ID"] in ["debian", "raspbian"]:
            with open("/etc/debian_version") as f:
                DEBIAN_VERSION = f.readline().strip()

            major_version = DEBIAN_VERSION.split(".")[0]
            version_split = os_release["VERSION"].split(" ", maxsplit=1)

            if version_split[0] == major_version:
                os_release["VERSION"] = " ".join([DEBIAN_VERSION] + version_split[1:])

        return os_release
    else:
        return None


PLATFORM_NAME = _platform_name()
LINUX_RELEASE = _linux_release()
