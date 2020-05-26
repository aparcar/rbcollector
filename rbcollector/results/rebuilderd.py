import logging

import requests

logger = logging.getLogger(__name__)


def get_rbvfs(config: dict, timestamp):
    logger.info("Using Rebuilderd")
    host = config["rebuilderd"]["host"]
    distro = config["rebuilderd"]["distro"]
    logger.debug(f"Rebuilderd at {host} for {distro}")

    results = requests.get(f"{host}/api/v0/pkgs/list?distro={distro}").json()

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
