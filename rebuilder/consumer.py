from datetime import datetime

import yaml
from peewee import *

import results.gitlab
import results.github
import results.rebuilderd
import sources.archlinux
import sources.openwrt
from database import *
from render import render_all

with open("config.yml") as config_file:
    config = yaml.safe_load(config_file)

init_db()

for name, origin_config in config.get("origins", {}).items():
    origin_data = dict(
        name=name,
        alias=origin_config["alias"],
        description=origin_config["description"],
        uri=origin_config["uri"],
        website=origin_config["website"],
    )
    Origins.insert(origin_data).on_conflict(
        conflict_target=[Origins.name], update=origin_data
    ).execute()

    origin = Origins.get(name=name)


for name, rebuilder_config in config.get("rebuilders", {}).items():
    rebuilder_data = dict(
        name=name,
        maintainer=rebuilder_config["maintainer"],
        contact=rebuilder_config["contact"],
        uri=rebuilder_config["uri"],
    )
    Rebuilders.insert(rebuilder_data).on_conflict(
        conflict_target=[Rebuilders.name], update=rebuilder_data
    ).execute()

results_methods = {
    "gitlab": results.gitlab.get_rbvfs,
    "github": results.github.get_rbvfs,
    "rebuilderd": results.rebuilderd.get_rbvfs,
}
sources_methods = {
    "archlinux": sources.archlinux.update_sources,
    "openwrt": sources.openwrt.update_sources,
}

target_map = {"x86_64": "x86/64"}


def insert_rbvf(rbvf: dict):
    rebuilder = Rebuilders.get_or_none(Rebuilders.name == rbvf["rebuilder"]["name"])

    if not rebuilder:
        print(f"Unknown rebuilder {rbvf['rebuilder']['name']}")
        return 1

    origin = Origins.get_or_none(name=rbvf.pop("origin_name"))

    if not origin:
        print(f"Unknown origin in {path}")
        return 1

    storage_uri, _ = Storages.get_or_create(uri=rbvf.pop("storage_uri", ""))

    for result in rbvf["results"]:
        artifacts, _ = Artifacts.get_or_create(**result.pop("artifacts"))
        suite = Suites.get_or_none(name=result.pop("suite"), origin=origin)
        if not suite:
            # print("skip unknown suite")
            continue

        component = Components.get_or_none(name=result.pop("component"), suite=suite)
        if not component:
            continue

        target = Targets.get_or_none(name=result.pop("target"), component=component)
        if not target:
            print(f"ERROR: target unknown")
            continue

        source = Sources.get_or_none(
            name=result.pop("name"), version=result.pop("version"), target=target,
        )
        if not source:
            print(f"ERROR: source unknown")
            continue

        result.pop("cpe", "")
        build_date = datetime.fromtimestamp(result.pop("build_date", 0))

        Results.insert(
            **result,
            artifacts=artifacts,
            rebuilder=rebuilder,
            source=source,
            build_date=build_date,
            storage_uri=storage_uri,
        ).on_conflict_ignore().execute()


for origin in Origins.select():
    print(f"Get sources of {origin.name}")
    origin_config = {**config["origins"][origin.name], "name": origin.name}
    sources_methods[origin_config["sources_method"]](origin_config, origin.timestamp)
    origin.update(timestamp=datetime.utcnow()).execute()

for rebuilder in Rebuilders.select():
    if rebuilder.name != "aparcar-openwrt-github":
        continue

    rebuilder_config = {**config["rebuilders"][rebuilder.name], "name": rebuilder.name}

    rbvfs = results_methods[rebuilder_config["results_method"]](
        rebuilder_config, rebuilder.timestamp
    )
    rebuilder.update(timestamp=datetime.now())
    for rbvf in rbvfs:
        insert_rbvf(rbvf)

render_all()
