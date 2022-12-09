import os
from pathlib import Path


def load_ae5_user_secrets(secrets_path: str = "/var/run/secrets/user_credentials/"):
    base_path: Path = Path(secrets_path)
    print(f"Loading environment variables from {base_path}:")
    for secret in base_path.glob("*"):
        if secret.is_file():
            print(secret.name)
            with open(file=secret, mode="r", encoding="utf-8") as file:
                os.environ[secret.name] = file.read()
