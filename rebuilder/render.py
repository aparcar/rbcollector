from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import yaml
from collections import namedtuple

from database import *

file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader, extensions=["jinja2.ext.do"])


def render_target(target):
    output_path = (
        Path().cwd()
        / "public"
        / target.component.suite.origin.name
        / target.component.suite.name
        / target.component.name
        / target.name
        / "index.html"
    )

    sources = (
        target.sources.select()
        .where(Sources.timestamp == target.timestamp)
        .order_by(Sources.name)
    )

    rebuilders = target.component.suite.origin.rebuilders

    template = env.get_template("target.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(
        template.render(target=target, sources=sources, rebuilders=rebuilders)
    )


def render_start(origins):
    output_path = Path().cwd() / "public/index.html"
    template = env.get_template("start.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(origins=origins))


def render_suites(origin):
    output_path = Path().cwd() / "public" / origin.name / "index.html"
    template = env.get_template("origin.html")
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


def render_rebuilders(rebuilders):
    output_path = Path().cwd() / "public/rebuilders.html"
    template = env.get_template("rebuilders.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(rebuilders=rebuilders))


def render_all(rebuilders):
    render_rebuilders(rebuilders)
    origins = Origins.select()
    render_start(origins)
    for origin in origins:
        print(f"Rendering {origin.name}")
        render_suites(origin)
        continue
        for suite in origin.suites:
            print(f"Rendering {origin.name}/{suite.name}")
            render_components(suite)
            for component in suite.components:
                print(f"Rendering {origin.name}/{suite.name}/{component.name}")
                for target in component.targets:
                    print(
                        f"Rendering {origin.name}/{suite.name}/{component.name}/{target.name}"
                    )
                    render_target(target)
