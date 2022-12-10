import json
from datetime import datetime, timedelta
from typing import Union

from mlflow import MlflowClient
from mlflow.entities import Experiment, Run
from mlflow.entities.model_registry import ModelVersion
from mlflow.store.entities import PagedList

from ..common.config.environment import demand_env_var_as_int
from ..dto.base_model import BaseModel
from ..dto.tracking.pruneable import Pruneable


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

    def get_prunable_runs(self, runs: list[Run]) -> list[Pruneable]:
        prunables: list[Pruneable] = []

        for run in runs:
            if run.info.end_time:
                run_id: str = run.info.run_id

                run_end_time: int = run.info.end_time / 1000
                run_end_time_dt: datetime = datetime.fromtimestamp(run_end_time)

                proto_pruneable: dict = {}

                if "mlflow.log-model.history" in run.data.tags:
                    model_meta = json.loads(run.data.tags["mlflow.log-model.history"])[0]
                    model_run_id: str = model_meta["run_id"]

                    # Pruneable runs
                    oldest_allowed_date: datetime = datetime.utcnow() - timedelta(
                        days=demand_env_var_as_int(name="MLFLOW_TRACKING_ENTITY_TTL")
                    )
                    if run_end_time_dt < oldest_allowed_date:
                        proto_pruneable["run"] = {"run_id": run_id}
                        model: Union[ModelVersion, None] = self.get_prunable_model(run_id=model_run_id)
                        if model:
                            proto_pruneable["model"] = {"name": model.name, "version": model.version}

                prunables.append(Pruneable.parse_obj(proto_pruneable))
        return prunables

    def delete_model_version(self, name: str, version: str, dry_run: bool = False) -> None:
        if dry_run:
            print(f"[Dry Run] Delete model version, name: {name}, version: {version}")
        else:
            print(f"Deleting model version, name: {name}, version: {version} ..")
            self.client.delete_model_version(name=name, version=version)

    def delete_run(self, id: str, dry_run: bool = False) -> None:
        if dry_run:
            print(f"[Dry Run] Delete experiment run, id: {id}")
        else:
            print(f"Deleting experiment run, id: {id} ..")
            self.client.delete_run(run_id=id)

    def get_pruneables(self) -> list[Pruneable]:
        experiments: list[Experiment] = self.get_experiments()
        pruneables: list[Pruneable] = []
        for experiment in experiments:
            print(f"Reviewing experiment {experiment.experiment_id}")
            runs: list[Run] = self.get_experiment_runs(experiment_id=experiment.experiment_id)
            pruneables = pruneables + self.get_prunable_runs(runs=runs)
        return pruneables

    def prune(self, pruneables: list[Pruneable], dry_run: bool = False) -> None:
        for pruneable in pruneables:
            if pruneable.model:
                self.delete_model_version(name=pruneable.model.name, version=pruneable.model.version, dry_run=dry_run)
            if pruneable.run:
                self.delete_run(id=pruneable.run.run_id, dry_run=dry_run)
