import shlex
import subprocess
import sys
from argparse import ArgumentParser

from dotenv import load_dotenv

from ....ae5.secrets import load_ae5_user_secrets
from ...client import AnacondaMlFlowClient
from ...service.factory import build_client, build_mlflow_client


def get_config_for_stage(stage_name: str) -> str:
    lower_name: str = stage_name.lower()
    if lower_name == "local":
        return "env/.env.local.pruner"
    if lower_name == "staging":
        return "env/.env.staging.pruner"
    if lower_name == "production":
        return "env/.env.production.pruner"

    exp_message: str = f"Unknown stage {stage_name} received"
    raise Exception(exp_message)


def launch(shell_out_cmd: str) -> None:
    args = shlex.split(shell_out_cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        sys.stdout.buffer.write(line)


def wrapped_prune():
    client: AnacondaMlFlowClient = build_client(client=build_mlflow_client())
    client.prune(pruneables=client.get_pruneables(), dry_run=False)


if __name__ == "__main__":
    # arg parser for the standard anaconda-project options
    parser = ArgumentParser(
        prog="mlflow-tracking-server-pruner-launch-wrapper", description="mlflow tracking server pruner launch wrapper"
    )
    parser.add_argument("--stage", action="store", help="The stage of the deployment")
    args = parser.parse_args(sys.argv[1:])
    print(args)

    # load defined environmental variables
    load_dotenv(dotenv_path=get_config_for_stage(stage_name=args.stage))
    load_ae5_user_secrets()

    # prune stale
    wrapped_prune()

    # perform mlflow garbage collection
    # https://www.mlflow.org/docs/latest/cli.html#mlflow-gc
    cmd: str = f"mlflow gc --older-than 10d0h0m0s"
    print(cmd)
    launch(shell_out_cmd=cmd)
