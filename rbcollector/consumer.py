import logging
import time
from datetime import datetime

import yaml
from peewee import *

import rbcollector.results.github
import rbcollector.results.gitlab
import rbcollector.results.rebuilderd
import rbcollector.sources.archlinux
import rbcollector.sources.openwrt
from rbcollector.database import *

with open("config.yml") as config_file:
    config = yaml.safe_load(config_file)

logger = logging.getLogger(__name__)

results_methods = {
    "gitlab": rbcollector.results.gitlab.get_rbvfs,
    "github": rbcollector.results.github.get_rbvfs,
    "rebuilderd": rbcollector.results.rebuilderd.get_rbvfs,
}
sources_methods = {
    "archlinux": rbcollector.sources.archlinux.update_sources,
    "openwrt": rbcollector.sources.openwrt.update_sources,
}


def insert_rbvf(rbvf: dict):
    rebuilder = Rebuilders.get_or_none(Rebuilders.name == rbvf["rebuilder"]["name"])

    if not rebuilder:
        print(f"Unknown rebuilder {rbvf['rebuilder']['name']}")
        return False

    origin_name = rbvf.get("origin_name")
    if not origin_name:
        logger.warning("origin_name missing in rbvf")
        return False
    origin = Origins.get_or_none(name=origin_name)

    if not origin:
        logger.warning(f"Unknown origin {origin_name}")
        return False

    storage_uri, _ = Storages.get_or_create(uri=rbvf.pop("storage_uri", ""))

    for result in rbvf["results"]:
        status = result.get("status")
        if not status:
            logger.warning("status mising")
            continue

        artifacts, _ = Artifacts.get_or_create(**result.pop("artifacts"))

        suite_name = result.get("suite")
        if not suite_name:
            logger.warning("suite mising")
            continue

        suite = Suites.get_or_none(name=suite_name, origin=origin)
        if not suite:
            logger.warning(f"skip unknown suite {suite_name}")
            continue

        component_name = result.get("component")
        if not component_name:
            logger.warning("component mising")
            continue

        component = Components.get_or_none(name=component_name, suite=suite)
        if not component:
            logger.warning(f"skip unknown component {component_name}")
            continue

        target_name = result.get("target")
        if not target_name:
            logger.warning("target mising")
            continue

        target = Targets.get_or_none(name=target_name, component=component)
        if not component:
            logger.warning(f"skip unknown target {target_name}")
            continue

        source_name = result.get("name")
        if not source_name:
            logger.warning("result source name mising")
            continue

        source_version = result.get("version")
        if not source_version:
            logger.warning("result source version mising")
            continue

        source = Sources.get_or_none(
            name=source_name, version=source_version, target=target
        )
        if not source:
            logger.warning(f"skip unknown source {result}")
            continue

        build_date = datetime.fromtimestamp(result.pop("build_date", 0))

        Results.insert(
            status=status,
            artifacts=artifacts,
            rebuilder=rebuilder,
            source=source,
            build_date=build_date,
            storage_uri=storage_uri,
        ).on_conflict(
            conflict_target=[Results.source, Results.rebuilder],
            update={Results.build_date: build_date},
        ).execute()


def update_origins():
    for origin in Origins.select():
        print(f"Get sources of {origin.name}")
        origin_config = {**config["origins"][origin.name], "name": origin.name}
        sources_methods[origin_config["sources_method"]](origin_config)


def update_rebuilder():
    for rebuilder in Rebuilders.select():
        rebuilder_config = {
            **config["rebuilders"][rebuilder.name],
            "name": rebuilder.name,
        }

        rbvfs = results_methods[rebuilder_config["results_method"]](
            rebuilder_config, rebuilder.timestamp
        )
        Rebuilders.update(timestamp=datetime.utcnow()).where(
            Rebuilders.id == rebuilder
        ).execute()

        for rbvf in rbvfs:
            insert_rbvf(rbvf)
