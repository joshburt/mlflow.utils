import shlex
import subprocess
import sys
from argparse import ArgumentParser

from dotenv import load_dotenv


def launch(shell_out_cmd: str) -> None:
    args = shlex.split(shell_out_cmd)
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in proc.stdout:
        sys.stdout.buffer.write(line)


def get_config_for_stage(stage_name: str) -> str:
    lower_name: str = stage_name.lower()
    if lower_name == "local":
        return "env/.env.local.tracking.server"
    if lower_name == "staging":
        return "env/.env.staging.tracking.server"
    if lower_name == "production":
        return "env/.env.production.tracking.server"

    exp_message: str = f"Unknown stage {stage_name} received"
    raise Exception(exp_message)


if __name__ == "__main__":
    # arg parser for the standard anaconda-project options
    parser = ArgumentParser(
        prog="mlflow-tracking-server-launch-wrapper", description="mlflow tracking server launch wrapper"
    )

    parser.add_argument("--anaconda-project-host", action="append", default=[], help="Hostname to allow in requests")
    parser.add_argument("--anaconda-project-port", action="store", default=8086, type=int, help="Port to listen on")
    parser.add_argument(
        "--anaconda-project-iframe-hosts",
        action="append",
        help="Space-separated hosts which can embed us in an iframe per our Content-Security-Policy",
    )
    parser.add_argument(
        "--anaconda-project-no-browser", action="store_true", default=False, help="Disable opening in a browser"
    )
    parser.add_argument(
        "--anaconda-project-use-xheaders", action="store_true", default=False, help="Trust X-headers from reverse proxy"
    )
    parser.add_argument("--anaconda-project-url-prefix", action="store", default="", help="Prefix in front of urls")
    parser.add_argument(
        "--anaconda-project-address",
        action="store",
        default="0.0.0.0",
        help="IP address the application should listen on.",
    )

    parser.add_argument("--stage", action="store", help="The stage of the deployment")

    args = parser.parse_args(sys.argv[1:])

    print(args)

    # https://www.mlflow.org/docs/latest/cli.html#mlflow-server

    # load defined environmental variables
    load_dotenv(dotenv_path=get_config_for_stage(stage_name=args.stage))

    cmd: str = (
        f"mlflow server --serve-artifacts --port {args.anaconda_project_port} --host {args.anaconda_project_address}"
    )
    print(cmd)
    launch(shell_out_cmd=cmd)
