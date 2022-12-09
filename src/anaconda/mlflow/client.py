import json
from datetime import datetime, timedelta
from typing import Union

from mlflow import MlflowClient
from mlflow.entities import Experiment, Run
from mlflow.entities.model_registry import ModelVersion
from mlflow.store.entities import PagedList

from ..dto.base_model import BaseModel

MAX_RUN_AGE: timedelta = timedelta(days=1)


class AnacondaMlFlowClient(BaseModel):
    client: MlflowClient

    def get_experiments(self) -> list[Experiment]:
        experiments: PagedList[Experiment] = PagedList(items=[], token=None)

        halt_paging: bool = False
        page_token: Union[str, None] = None
        while not halt_paging:
            reported_experiments: PagedList[Experiment] = self.client.search_experiments(page_token=page_token)
            if reported_experiments.token is not None:
                page_token = reported_experiments.token
            else:
                halt_paging = True
            experiments.append(reported_experiments)

        return list(experiments[0])

    def get_experiment_runs(self, experiment_id: str) -> list[Run]:
        results: PagedList[Run] = PagedList(items=[], token=None)

        halt_paging: bool = False
        page_token: Union[str, None] = None
        while not halt_paging:
            reported_runs: PagedList[Run] = self.client.search_runs(
                experiment_ids=[experiment_id], page_token=page_token
            )
            if reported_runs.token is not None:
                page_token = reported_runs.token
            else:
                halt_paging = True
            results.append(reported_runs)

        return list(results[0])

    def get_prunable_model(self, run_id: str) -> Union[ModelVersion, None]:
        model_list: PagedList[ModelVersion] = self.client.search_model_versions(f"run_id = '{run_id}'")

        # There should only be a single match
        if len(model_list) != 1:
            return None

        model_version: ModelVersion = model_list[0]

        # We only want to pull models which have no stage (meaning not staging, production, or archived).
        if model_version.current_stage != "None":
            return None

        return model_version

    def get_prunable_runs(self, runs: list[Run]) -> list[dict]:
        prunables: list[dict] = []
        for run in runs:
            if run.info.end_time:
                run_id: str = run.info.run_id

                run_end_time: int = run.info.end_time / 1000
                run_end_time_dt: datetime = datetime.fromtimestamp(run_end_time)

                model_meta = json.loads(run.data.tags["mlflow.log-model.history"])[0]
                model_run_id: str = model_meta["run_id"]

                # Prunable runs
                MAX_AGE_TIME: datetime = datetime.utcnow() - MAX_RUN_AGE
                if run_end_time_dt < MAX_AGE_TIME:
                    model: Union[ModelVersion, None] = self.get_prunable_model(run_id=model_run_id)
                    if model:
                        # At this point both the run and model are prunable.
                        prunable: dict = {
                            "experiment_run_id": run_id,
                            "model": {"name": model.name, "version": model.version},
                        }
                        prunables.append(prunable)
        return prunables

    def prune(self) -> None:
        experiments: list[Experiment] = self.get_experiments()
        for experiment in experiments:
            print(f"Reviewing experiment {experiment.experiment_id}")
            runs: list[Run] = self.get_experiment_runs(experiment_id=experiment.experiment_id)
            prunables = self.get_prunable_runs(runs=runs)
            print(prunables)
