import logging
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from rbcollector.database import *

logger = logging.getLogger(__name__)

file_loader = FileSystemLoader(Path(__file__).parent.absolute() / "templates")
env = Environment(loader=file_loader, extensions=["jinja2.ext.do"])


def render_target(work_path, target):
    output_path = (
        work_path
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


def render_start(work_path, origins):
    output_path = work_path / "index.html"
    template = env.get_template("start.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(origins=origins))


def render_suites(work_path, origin):
    output_path = work_path / origin.name / "index.html"
    template = env.get_template("origin.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(origin=origin))


def render_components(work_path, suite):
    output_path = work_path / suite.origin.name / suite.name / "index.html"
    template = env.get_template("components.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(suite=suite))


def render_targets(work_path, component, targets):
    output_path = (
        work_path
        / component.suite.origin.name
        / component.suite.name
        / component.name
        / "index.html"
    )
    template = env.get_template("sources.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(component=component, targets=targets))


def render_rebuilders(work_path, rebuilders):
    output_path = work_path / "rebuilders.html"
    template = env.get_template("rebuilders.html")
    output_path.parent.mkdir(exist_ok=True, parents=True)
    output_path.write_text(template.render(rebuilders=rebuilders))


def site(rebuilders, dir="./public"):
    logger.info(f"Rendering site to {dir}")
    work_path = Path(dir)
    work_path.mkdir(exist_ok=True, parents=True)
    render_rebuilders(work_path, rebuilders)

    origins = Origins.select()
    render_start(work_path, origins)
    for origin in origins:
        logger.info(f"Rendering {origin.name}")
        render_suites(work_path, origin)

        for suite in origin.suites:
            logger.info(f"Rendering {origin.name}/{suite.name}")
            render_components(work_path, suite)

            for component in suite.components:
                logger.info(f"Rendering {origin.name}/{suite.name}/{component.name}")

                for target in component.targets:
                    logger.info(
                        f"Rendering {origin.name}/{suite.name}/{component.name}/{target.name}"
                    )
                    render_target(work_path, target)
    
    shutil.copytree(Path(__file__).parent.absolute() / "static", work_path / "static", dirs_exist_ok=True)
