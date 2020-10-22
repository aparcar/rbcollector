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

    for suite in config["web"]["suites"]:
        for target in config["web"]["targets"]:
            target_url = f"{config['web']['base_url']}/{suite}/{target}"
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
