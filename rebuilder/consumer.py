from datetime import datetime
import gzip
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import gitlab
from jinja2 import Environment, FileSystemLoader
from peewee import *

import sources.archlinux
import sources.openwrt
import results.gitlab
import results.rebuilderd

from database import *


import yaml

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


for name, rebuilder in config.get("rebuilders", {}).items():
    Rebuilders.insert(**rebuilder, name=name).on_conflict(
        conflict_target=[Rebuilders.name], update=rebuilder
    ).execute()

results_methods = {
    "gitlab": results.gitlab.get_rbvfs,
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
        print(f"Unknown rebuilder in {path}: {rbvf['rebuilder']['name']}")
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

        tested_version = result.pop("version")
        target = result.pop("target")

        source = Sources.get_or_none(
            name=result.pop("name"),
            version=tested_version,
            component=component,
            target=target,
        )
        if not source:
            print(f"ERROR: source unknown")
            continue

        result.pop("cpe", "")
        build_date = datetime.fromtimestamp(result.pop("build_date", 0))

        Results.get_or_create(
            **result,
            artifacts=artifacts,
            rebuilder=rebuilder,
            source=source,
            tested_version=tested_version,
            build_date=build_date,
            storage_uri=storage_uri,
        )


file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)


def render_target(origin, suite, component, target):
    sources = (
        Sources()
        .select()
        .join(Components)
        .join(Suites)
        .join(Origins)
        .where(
            Origins.name == origin,
            Suites.name == suite,
            Components.name == component,
            Sources.target == target,
        )
    )

    output_path = (
        Path().cwd() / "public" / origin / suite / component / target / "index.html"
    )

    template = env.get_template("target.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(sources=sources))


def render_origins(origins):
    output_path = Path().cwd() / "public/index.html"
    template = env.get_template("origins.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(origins=origins))


def render_suites(origin):
    output_path = Path().cwd() / "public" / origin.name / "index.html"
    template = env.get_template("suites.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(origin=origin))


def render_components(suite):
    output_path = (
        Path().cwd() / "public" / suite.origin.name / suite.name / "index.html"
    )
    template = env.get_template("components.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(suite=suite))


def render_targets(component, targets):
    output_path = (
        Path().cwd()
        / "public"
        / component.suite.origin.name
        / component.suite.name
        / component.name
        / "index.html"
    )
    template = env.get_template("sources.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(component=component, targets=targets))


def render():
    origins = Origins.select()
    render_origins(origins)
    for origin in origins:
        print(f"Rendering {origin.name}")
        render_suites(origin)
        for suite in origin.suites:
            print(f"Rendering {origin.name}/{suite.name}")
            render_components(suite)
            for component in suite.components:
                targets = component.sources.select(Sources.target).distinct()
                render_targets(component, targets)
                for target in targets:
                    render_target(
                        origin.name, suite.name, component.name, target.target
                    )


origins = Origins.select().execute()

for origin in origins:
   origin_config = config["origins"][origin.name]
   sources_methods[origin_config["sources_method"]](origin.name, origin_config)
   origin.update(timestamp=datetime.now())

for rebuilder in Rebuilders.select():
    rbvfs = results_methods[rebuilder.results_method](
        {**config, "name": rebuilder.name}, rebuilder.uri, rebuilder.timestamp
    )
    rebuilder.update(timestamp=datetime.now())
    for rbvf in rbvfs:
        insert_rbvf(rbvf)

render()
