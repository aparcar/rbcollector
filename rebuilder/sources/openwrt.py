import email.parser
from os import environ
from urllib.request import urlopen
import re

from rebuilder.database import *


def get_target_url(uri, version, target):
    if version == "SNAPSHOT":
        print("Using snapshots/")
        return f"{uri}/snapshots/targets/{target}"
    else:
        print(f"Using releases/{version}/")
        return f"{uri}/releases/{version}/targets/{target}"


def parse_origin_images(uri, version, target):
    return re.findall(
        f".+? \*(openwrt-{target.replace('/', '-')}.+?.)\n",
        urlopen(get_target_url(uri, version, target) + "/sha256sums").read().decode(),
    )


def parse_origin_packages(uri, version, target):
    packages = []
    linebuffer = ""
    for line in (
        urlopen(get_target_url(uri, version, target) + "/packages/Packages")
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


def update_packages(name, config, suite_name, target):
    origin = Origins.get(name=name)
    suite, _ = Suites.get_or_create(name=suite_name, origin=origin)
    component, _ = Components.get_or_create(name="packages", suite=suite)

    for source in parse_origin_packages(config["uri"], suite_name, target):
        Sources.get_or_create(
            name=source["Package"],
            version=source["Version"],
            component=component,
            target=target,
            cpe=source.get("CPE-ID", ""),
        )


def update_images(name, config, suite_name, target):
    origin = Origins.get(name=name)
    suite, _ = Suites.get_or_create(name=suite_name, origin=origin)
    component, _ = Components.get_or_create(name="images", suite=suite)

    version = (
        urlopen(
            get_target_url(config.get("uri"), suite_name, target) + "/version.buildinfo"
        )
        .read()
        .decode()
        .strip()
        .split("-")[1]
    )

    for image in parse_origin_images(config["uri"], suite_name, target):
        Sources.get_or_create(
            name=image, version=version, component=component, target=target, cpe="",
        )


def update_sources(name, config):
    print(config)
    for suite in config.get("suites"):
        for target in config.get("targets"):
            update_images(name, config, suite, target)
            update_packages(name, config, suite, target)
