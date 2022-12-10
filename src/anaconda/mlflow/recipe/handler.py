import shlex
import subprocess
import sys

from mlflow.recipes import Recipe

from ...ae5.secrets import load_ae5_user_secrets


def launch(shell_out_cmd: str) -> None:
    args = shlex.split(shell_out_cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        sys.stdout.buffer.write(line)


def launch_recipe(profile: str = "ae5"):
    recipe: Recipe = Recipe(profile=profile)
    recipe.run()


if __name__ == "__main__":
    # load defined environmental variables
    load_ae5_user_secrets()

    # launch recipe
    launch_recipe()
