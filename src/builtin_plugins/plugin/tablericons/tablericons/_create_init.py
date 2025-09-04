import glob
import os

ReservedNames = {"lambda"}


def main() -> None:
    package_path = os.path.dirname(__file__)

    with open(os.path.join(package_path, "__init__.py"), "w") as f:
        f.write(
            f"""import os

_package_path = os.path.dirname(__file__)


def _get_path(group: str, name: str) -> str:
    return os.path.join(_package_path, "_resources", group, name)


"""
        )

        resources_path = os.path.join(package_path, "_resources")
        for group in os.listdir(resources_path):
            f.write(f"class {group}:\n")
            group_path = os.path.join(resources_path, group)
            for path in glob.glob(os.path.join(glob.escape(group_path), "*.svg")):
                base_name = os.path.basename(path)
                variable: str = os.path.splitext(base_name)[0].replace("-", "_")
                while variable in ReservedNames:
                    variable += "_"
                if not variable.isidentifier():
                    raise RuntimeError(f"{variable} is not a valid python identifier.")
                f.write(f'    {variable} = _get_path("{group}", "{base_name}")\n')


if __name__ == "__main__":
    main()
