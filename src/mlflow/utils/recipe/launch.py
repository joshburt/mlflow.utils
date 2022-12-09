import shlex
import subprocess
import sys

from common.utils.secrets import load_ae5_user_secrets
from mlflow.recipes import Recipe


def launch_recipe():
    recipe: Recipe = Recipe(profile="ae5")
    recipe.run()


if __name__ == "__main__":
    # Setup our environment
    load_ae5_user_secrets()

    # Run the recipe.
    launch_recipe()
