import gzip
import json
from json.decoder import JSONDecodeError
import shutil
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
import logging

import requests

logger = logging.getLogger(__name__)


def get_rbvfs(config, timestamp):
    logger.info("Using generic web")
    rbvfs = []

    for suite in config["web"].get("suites", ["unset-suite"]):
        logger.debug(f"Check suite {suite}")
        for component in config["web"].get("components", ["unset-component"]):
            logger.debug(f"Check component {component}")
            for target in config["web"].get("targets", ["unset-target"]):
                logger.debug(f"Check target {target}")
                target_url = config["web"]["base_url"].format(
                    suite=suite, target=target, component=component
                )

                try:
                    logger.info(f"Downloading {target_url}/rbvf.json")
                    rbvf = requests.get(f"{target_url}/rbvf.json").json()
                except JSONDecodeError:
                    logger.warning(f"Failed to download rbvf.json")
                    continue

                if "timestamp" in rbvf:
                    remote_timestamp = datetime.fromisoformat(
                        rbvf["timestamp"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    if remote_timestamp < timestamp:
                        logger.info(
                            "Local timestamp {timestamp} is equal or newer than {remote_timestamp}"
                        )
                        continue

                rbvf["storage_uri"] = target_url
                rbvfs.append(rbvf)

    return rbvfs
