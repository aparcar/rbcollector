from json.decoder import JSONDecodeError
import logging
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
        "origin_name": "archlinux",
        "results": [],
        "rebuilder": {"name": config["name"]},
    }

    for result in results:
        status = "unreproducible"
        if result["status"] == "GOOD":
            status = "reproducible"
        rbvf["results"].append(
            {
                "suite": result["suite"],
                "component": "packages",
                "target": result["architecture"],
                "name": result["name"],
                "version": result["version"],
                "status": status,
                "artifacts": {},
                "build_date": 0,
                "build_duration": 0,
            }
        )

    return [rbvf]
