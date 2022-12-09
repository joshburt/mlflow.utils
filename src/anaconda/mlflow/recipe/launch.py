from mlflow.recipes import Recipe


def launch_recipe(profile: str = "ae5"):
    recipe: Recipe = Recipe(profile=profile)
    recipe.run()
