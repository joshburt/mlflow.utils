import os
import sys
from argparse import ArgumentParser
from pathlib import Path


def load_ae5_user_secrets(secrets_path: str = "/var/run/secrets/user_credentials/"):
    base_path: Path = Path(secrets_path)
    print(f"Loading environment variables from {base_path}:")
    for secret in base_path.glob("*"):
        if secret.is_file():
            print(secret.name)
            with open(file=secret, mode="r", encoding="utf-8") as file:
                os.environ[secret.name] = file.read()


if __name__ == "__main__":
    # arg parser for the standard anaconda-project options
    parser = ArgumentParser(
        prog="ae5-secrets-loader",
        description="Loads AE5 managed secrets into environment variables",
    )
    parser.add_argument(
        "--anaconda-secrets-path",
        action="store",
        default="/var/run/secrets/user_credentials/",
        help="The system path to load secrets from.",
    )

    args = parser.parse_args(sys.argv[1:])
    load_ae5_user_secrets(secrets_path=args.anaconda_secrets_path)
