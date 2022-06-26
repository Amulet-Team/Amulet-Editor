import json
import os
import sys
import subprocess

if __name__ == "__main__":

    with open(
        os.path.join(os.getcwd(), "src", "build", "settings", "base.json")
    ) as json_file:
        main_module = json.load(json_file)["main_module"]

    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "src", "main", "python")

    subprocess.run([sys.executable, os.path.join(os.getcwd(), main_module)], env=env)
