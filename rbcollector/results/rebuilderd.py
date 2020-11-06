import logging
from json.decoder import JSONDecodeError
from dateutil.parser import parse

import requests

logger = logging.getLogger(__name__)


def get_rbvfs(config: dict, timestamp):
    logging.info("Using Rebuilderd")
    host = config["rebuilderd"]["host"]
    distro = config["rebuilderd"]["distro"]

    try:
        rbvf_url = f"{host}/api/v0/pkgs/list?distro={distro}"
        logger.info(f"Downloading {rbvf_url}")
        results = requests.get(rbvf_url).json()
    except JSONDecodeError:
        logger.warning(f"Failed to download rbvf.json")
        return []

    rbvf = {
        "origin_uri": "",
        "origin_name": distro,
        "results": [],
        "rebuilder": {"name": config["name"]},
    }

    for result in results:
        if result["status"] == "GOOD":
            status = "reproducible"
        else:
            status = "unreproducible"

        rbvf_result = {
            "suite": result["suite"],
            "component": "packages",
            "target": result["architecture"],
            "name": result["name"],
            "version": result["version"],
            "status": status,
            "artifacts": {},
            "build_duration": 0,
        }

        if result.get("build_at"):
            rbvf_result["build_date"] = int(parse(result["build_at"]).timestamp())
        else:
            rbvf_result["build_date"] = 0

        rbvf["results"].append(rbvf_result)

    return [rbvf]
