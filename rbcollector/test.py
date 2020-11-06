import json
from collections import namedtuple
from pathlib import Path

import yaml
from database import *
from jinja2 import Environment, FileSystemLoader


def dump():
    maintainers = Maintainers.select()
    Path("maintainers.json").write_text(json.dumps(list(maintainers.dicts())))

    origins = Origins.select()
    Path("origins.json").write_text(json.dumps(list(origins.dicts())))
    for origin in origins:
        Path("suites.json").write_text(json.dumps(list(origin.suites.dicts())))
        for suite in origin.suites:
            Path("components.json").write_text(
                json.dumps(list(suite.components.dicts()))
            )
            for component in suite.components:
                Path("targets.json").write_text(
                    json.dumps(list(component.targets.dicts()), default=str)
                )
                for target in component.targets:
                    Path("sources.json").write_text(
                        json.dumps(list(target.sources.dicts()), default=str)
                    )
                    return


def load():
    Origins.insert(json.loads(Path("origins.json").read_text())).execute()
    Maintainers.insert(json.loads(Path("maintainers.json").read_text())).execute()
    Suites.insert(json.loads(Path("suites.json").read_text())).execute()
    Components.insert(json.loads(Path("components.json").read_text())).execute()
    Targets.insert(json.loads(Path("targets.json").read_text())).execute()
    Sources.insert(json.loads(Path("sources.json").read_text())).execute()
