import email.parser
from os import environ
import re
import requests

from rbcollector.database import *
from email.utils import getaddresses


def get_target_url(uri, version, target):
    if version == "SNAPSHOT":
        return f"{uri}/snapshots/targets/{target}"
    else:
        return f"{uri}/releases/{version}/targets/{target}"


def parse_origin_images(uri, version, target_name):
    return re.findall(
        f".+? \*(openwrt-.*?{target_name.replace('/', '-')}.+?.)\n",
        requests.get(get_target_url(uri, version, target_name) + "/sha256sums").text,
    )


def parse_origin_packages(packages_text):
    packages = []
    linebuffer = ""
    for line in packages_text.splitlines():
        if line == "":
            parser = email.parser.Parser()
            package = parser.parsestr(linebuffer)
            packages.append(package)
            linebuffer = ""
        else:
            linebuffer += line + "\n"
    return packages


def update_packages(name, config, suite_name, target_name):
    origin = Origins.get(name=name)
    suite, _ = Suites.get_or_create(name=suite_name, origin=origin)
    component, _ = Components.get_or_create(name="packages", suite=suite)
    target, _ = Targets.get_or_create(name=target_name, component=component)

    packages_req = requests.get(
        get_target_url(config["uri"], suite_name, target_name)
        + "/packages/Packages.manifest"
    )

    last_modified = datetime.strptime(
        packages_req.headers.get("last-modified"), "%a, %d %b %Y %H:%M:%S %Z"
    )

    if target.timestamp >= last_modified:
        print(f"No source updates for {suite_name}/{component.name}/{target.name}")
        return

    for source in parse_origin_packages(packages_req.text):
        maintainers = getaddresses([source.get("Maintainer", "")])
        if maintainers:
            maintainer, _ = Maintainers.get_or_create(
                email=maintainers[0][1], name=maintainers[0][0]
            )
        else:
            maintainer = None

        Sources.insert(
            name=source["Package"],
            version=source["Version"],
            target=target,
            cpe=source.get("CPE-ID", ""),
            maintainer=maintainer,
            timestamp=last_modified,
        ).on_conflict(
            conflict_target=[Sources.name, Sources.version, Sources.target],
            update={
                Sources.timestamp: last_modified,
                Sources.maintainer: maintainer,
            },
        ).execute()

    Targets.update(timestamp=last_modified).where(Targets.id == target).execute()


def update_images(name, config, suite_name, target_name):
    origin = Origins.get(name=name)
    suite, _ = Suites.get_or_create(name=suite_name, origin=origin)
    component, _ = Components.get_or_create(name="images", suite=suite)
    target, _ = Targets.get_or_create(name=target_name, component=component)

    version_req = requests.get(
        get_target_url(config.get("uri"), suite_name, target_name)
        + "/version.buildinfo"
    )

    last_modified = datetime.strptime(
        version_req.headers.get("last-modified"), "%a, %d %b %Y %H:%M:%S %Z"
    )

    if target.timestamp >= last_modified:
        print(f"No source updates for {suite_name}/{component.name}/{target.name}")
        return

    version = version_req.text.strip().split("-")[1]

    for image in parse_origin_images(config["uri"], suite_name, target_name):
        Sources.insert(
            name=image,
            version=version,
            target=target,
            cpe="",
            timestamp=last_modified,
        ).on_conflict(
            conflict_target=[Sources.name, Sources.version, Sources.target],
            update={Sources.timestamp: last_modified},
        ).execute()

    Targets.update(timestamp=last_modified).where(Targets.id == target).execute()


def update_sources(config):
    print(config)
    for suite in config.get("suites"):
        for target in config.get("targets"):
            update_images(config["name"], config, suite, target)
            update_packages(config["name"], config, suite, target)
