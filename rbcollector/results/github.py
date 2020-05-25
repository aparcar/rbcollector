import gzip
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime

import requests


def get_rbvfs(config: dict, timestamp):
    print("Using GitHub")
    rbvfs = []
    headers = {"Authorization": "token " + config["github"]["token"]}
    response = requests.get(
        f"https://api.github.com/repos/{config['github']['repo']}/actions/artifacts"
    ).json()
    for artifact in response["artifacts"]:
        if artifact["expired"]:
            continue
        job_stamp = datetime.fromisoformat(
            artifact["created_at"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        if job_stamp < timestamp:
            continue

        with tempfile.TemporaryDirectory() as tmpdirname:
            print(f"Downloading to {artifact['name']}")

            tmp_path = Path(tmpdirname)
            zip_path = tmp_path / f"artifact_{artifact['id']}.zip"

            zip_path.write_bytes(
                requests.get(artifact["archive_download_url"], headers=headers).content
            )
            zip_file = zipfile.ZipFile(zip_path)
            zip_file.extractall(path=tmp_path)
            print(tmp_path)
            zip_file.close()

            rbvf_path = tmp_path / config["github"]["path"]
            if rbvf_path.is_file():
                if rbvf_path.suffix == ".gz":
                    with open(rbvf_path.with_suffix(""), "wb") as f_out:
                        with gzip.open(rbvf_path, "rb") as f_in:
                            shutil.copyfileobj(f_in, f_out)
                    rbvf_path = rbvf_path.with_suffix("")
                rbvf = json.loads(rbvf_path.read_text())
                rbvfs.append(rbvf)
            else:
                print(f"WARNING: rbvf file {rbvf_path} not found")

    return rbvfs
