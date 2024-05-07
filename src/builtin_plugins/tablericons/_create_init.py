import glob
import os


DigitAlt = {
    "0": "zero_",
    "1": "one_",
    "2": "two_",
    "3": "three_",
    "4": "four_",
    "5": "five_",
    "6": "six_",
    "7": "seven_",
    "8": "eight_",
    "9": "nine_",
}


def main():
    package_path = os.path.dirname(__file__)
    lines = []
    for path in glob.glob(
        os.path.join(glob.escape(package_path), "_resources", "*.svg")
    ):
        base_name = os.path.basename(path)
        variable: str = os.path.splitext(base_name)[0].replace("-", "_")
        if variable[0] in DigitAlt:
            variable = DigitAlt[variable[0]] + variable[1:]
        if not variable.isidentifier():
            raise RuntimeError(f"{variable} is not a valid python identifier.")
        lines.append(f'{variable} = _get_path("{base_name}")')

    lines_s = "\n".join(lines)

    with open(os.path.join(package_path, "__init__.py"), "w") as f:
        f.write(
            f"""import os

_package_path = os.path.dirname(__file__)


def _get_path(name):
    return os.path.join(_package_path, "_resources", name)


{lines_s}
"""
        )


if __name__ == "__main__":
    main()
