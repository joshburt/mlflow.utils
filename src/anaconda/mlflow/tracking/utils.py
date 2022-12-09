import mlflow
from mlflow.pyfunc import PyFuncModel


def load_model(model_name: str, model_version: int) -> PyFuncModel:
    model_uri: str = f"models:/{model_name}/{model_version}"
    return load_model_by_run(logged_model=model_uri)


def load_model_by_run(logged_model: str) -> PyFuncModel:
    return mlflow.pyfunc.load_model(model_uri=logged_model)
