import json
import logging
from collections import namedtuple
from os import environ
from pathlib import Path
from subprocess import run

import yaml
from jinja2 import Environment, FileSystemLoader

from rbcollector.database import *

logger = logging.getLogger(__name__)


def run_command(cmd, cwd=".", ignore_errors=False, capture=False, env={}, timeout=None):
    """
    Run a command in shell
    """
    print("Running {} in {}".format(cmd, cwd))
    current_env = environ.copy()
    current_env.update(env)
    proc = run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        env=current_env,
        timeout=timeout,
    )

    if proc.returncode and not ignore_errors:
        print("Error running {}".format(cmd))
        quit()

    if capture:
        print(proc.stderr)
        return proc.stdout


def dump(dir="./", all=False):
    work_path = Path(dir)
    work_path.mkdir(exist_ok=True, parents=True)

    maintainers = Maintainers.select()
    (work_path / "maintainers.json").write_text(json.dumps(list(maintainers.dicts())))

    origins = Origins.select()
    (work_path / "origins.json").write_text(json.dumps(list(origins.dicts())))
    for origin in origins:
        (work_path / "suites.json").write_text(json.dumps(list(origin.suites.dicts())))
        for suite in origin.suites:
            (work_path / "components.json").write_text(
                json.dumps(list(suite.components.dicts()))
            )
            for component in suite.components:
                (work_path / "targets.json").write_text(
                    json.dumps(list(component.targets.dicts()), default=str)
                )
                for target in component.targets:
                    (work_path / "sources.json").write_text(
                        json.dumps(list(target.sources.dicts()), default=str)
                    )
                    if not all:
                        return


def load(dir):
    work_path = Path(dir)
    if not work_path.is_dir():
        logger.error(f"Director {dir} not found")
        quit(1)
    init_db()
    Origins.insert(json.loads((work_path / "origins.json").read_text())).execute()
    Maintainers.insert(
        json.loads((work_path / "maintainers.json").read_text())
    ).execute()
    Suites.insert(json.loads((work_path / "suites.json").read_text())).execute()
    Components.insert(json.loads((work_path / "components.json").read_text())).execute()
    Targets.insert(json.loads((work_path / "targets.json").read_text())).execute()
    Sources.insert(json.loads((work_path / "sources.json").read_text())).execute()

