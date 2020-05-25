import json
from urllib.request import urlopen


def get_rbvfs(config: dict, timestamp):
    print("Using Rebuilderd")
    host, distro = config["uri"].split("#")
    results = json.loads(
        urlopen(f"{host}/api/v0/pkgs/list?distro={distro}").read().decode()
    )

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
