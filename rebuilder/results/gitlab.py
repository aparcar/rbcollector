import datetime
import gzip
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import gitlab


def get_rbvfs(config: dict, timestamp):
    print("Using GitLab")
    gl = gitlab.Gitlab(
        config["gitlab"]["host"], private_token=config["gitlab"]["token"]
    )
    project = gl.projects.get(config["gitlab"]["repo"].replace("/", "%2F"))
    jobs = project.jobs.list()
    rbvfs = []
    for job in jobs:
        job_stamp = datetime.datetime.fromisoformat(
            job.finished_at.replace("Z", "+00:00")
        )
        if job_stamp.replace(tzinfo=None) < timestamp.replace(tzinfo=None):
            break

        if job.status == "success":
            with tempfile.TemporaryDirectory() as tmpdirname:
                tmp_path = Path(tmpdirname)
                zip_path = tmp_path / f"job_{job.name}-{job.id}.zip"
                print(f"Downloading to {zip_path}")

                with open(zip_path, "wb") as f:
                    job.artifacts(streamed=True, action=f.write)
                zip = zipfile.ZipFile(zip_path)
                zip.extractall(path=tmp_path)
                rbvf_path = tmp_path / config["gitlab"]["path"]
                if rbvf_path.is_file():
                    if rbvf_path.suffix == ".gz":
                        with open(rbvf_path.with_suffix(""), "wb") as f_out:
                            with gzip.open(rbvf_path, "rb") as f_in:
                                shutil.copyfileobj(f_in, f_out)
                        rbvf_path = rbvf_path.with_suffix("")
                    rbvf = json.loads(rbvf_path.read_text())
                    rbvf["storage_uri"] = f"{job.web_url}/artifacts/file/"
                    rbvfs.append(rbvf)
                else:
                    print(f"WARNING: rbvf file {rbvf_path} not found")
    return rbvfs
