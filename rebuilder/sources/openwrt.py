import email.parser
from os import environ
from urllib.request import urlopen
import re

from rebuilder.database import *


def get_target_url(uri, version, target):
    if version == "SNAPSHOT":
        return f"{uri}/snapshots/targets/{target}"
    else:
        return f"{uri}/releases/{version}/targets/{target}"


def parse_origin_images(uri, version, target_name):
    return re.findall(
        f".+? \*(openwrt-{target_name.replace('/', '-')}.+?.)\n",
        urlopen(get_target_url(uri, version, target_name) + "/sha256sums")
        .read()
        .decode(),
    )


def parse_origin_packages(uri, version, target_name):
    packages = []
    linebuffer = ""
    for line in (
        urlopen(get_target_url(uri, version, target_name) + "/packages/Packages")
        .read()
        .decode()
        .splitlines()
    ):
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

    for source in parse_origin_packages(config["uri"], suite_name, target_name):
        Sources.get_or_create(
            name=source["Package"],
            version=source["Version"],
            target=target,
            cpe=source.get("CPE-ID", ""),
        )


def update_images(name, config, suite_name, target_name):
    origin = Origins.get(name=name)
    suite, _ = Suites.get_or_create(name=suite_name, origin=origin)
    component, _ = Components.get_or_create(name="images", suite=suite)
    target, _ = Targets.get_or_create(name=target_name, component=component)

    version = (
        urlopen(
            get_target_url(config.get("uri"), suite_name, target_name)
            + "/version.buildinfo"
        )
        .read()
        .decode()
        .strip()
        .split("-")[1]
    )

    for image in parse_origin_images(config["uri"], suite_name, target_name):
        Sources.get_or_create(
            name=image, version=version, target=target, cpe="",
        )


def update_sources(config, timestamp):
    print(config)
    for suite in config.get("suites"):
        for target in config.get("targets"):
            update_images(config["name"], config, suite, target)
            update_packages(config["name"], config, suite, target)
