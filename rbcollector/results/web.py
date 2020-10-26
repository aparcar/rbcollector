import gzip
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime

import requests


def get_rbvfs(config, timestamp):
    print("Using generic web")
    rbvfs = []

    for suite in config["web"].get("suites", ["unset-suite"]):
        for component in config["web"].get("components", ["unset-component"]):
            for target in config["web"].get("targets", ["unset-target"]):
                target_url = config["web"]["base_url"].format(
                    suite=suite, target=target, component=component
                )
                rbvf = requests.get(f"{target_url}/rbvf.json").json()

                if "timestamp" in rbvf:
                    if (
                        datetime.fromisoformat(
                            rbvf["timestamp"].replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                        < timestamp
                    ):
                        continue

                rbvf["storage_uri"] = target_url
                rbvfs.append(rbvf)

    return rbvfs
