import datetime
import gzip
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import gitlab


def get_rbvfs(config: dict, uri: str, timestamp):
    host, project = uri.split("#")
    gl = gitlab.Gitlab(host, private_token=config.get("gitlab_token"))
    project = gl.projects.get(project.replace("/", "%2F"))
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
                rbvf_path = tmp_path / "output/rbvf.json.gz"
                if rbvf_path.is_file():
                    with open(rbvf_path.with_suffix(""), "wb") as f_out:
                        with gzip.open(rbvf_path, "rb") as f_in:
                            shutil.copyfileobj(f_in, f_out)
                    rbvf = json.loads(rbvf_path.with_suffix("").read_text())
                    rbvf["storage_uri"] = f"{job.web_url}/artifacts/file/"
                    rbvfs.append(rbvf)
    return rbvfs
