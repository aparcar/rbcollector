import logging
import time

import click
import yaml

import rbcollector.consumer
import rbcollector.render
import rbcollector.util

with open("config.yml") as c:
    config = yaml.safe_load(c.read())

logger = logging.getLogger(__name__)
logging.basicConfig(level=config["log"]["level"])


@click.group()
def cli():
    logger.info("Starting CLI")


@cli.command()
@click.option(
    "-d", "--dir", "dir", default="./public", help="Directory to store rendered website"
)
def loop(dir):
    """Infinite loop to update sources, results and render site"""
    logger.info(f"Run loop forever")
    while True:
        rbcollector.consumer.update_origins()
        rbcollector.consumer.update_rebuilder()
        rbcollector.render.site(config["rebuilders"], dir)
        time.sleep(config["loop_interval"] * 60)


@cli.command()
@click.option(
    "-d", "--dir", "dir", default="./public", help="Directory to store rendered website"
)
def render_site(dir):
    rbcollector.render.site(config["rebuilders"], dir)
    logger.info(f"Finished rendering site in {dir}")


@cli.group()
def util():
    """Utilities to manage the rebuild-collector"""
    pass


@util.command()
def init_db():
    logger.info("Init database")
    rbcollector.database.init_db()


@util.command()
@click.option(
    "-d", "--dir", "dir", default="./", help="Directory to store database dump"
)
@click.option(
    "-a", "--all", "all", is_flag=True, default=False, help="Dump more than one target"
)
def dump_json(dir, all):
    """Dump (fraction) of database to JSON"""
    rbcollector.util.dump(dir, all)
    logger.info("Dumped database to JSON")


@util.command()
@click.option(
    "-d", "--dir", "dir", default="./", help="Directory to load database dump"
)
def load_json(dir):
    """Load database from JSON"""
    rbcollector.util.load(dir)
    logger.info("Loaded database from JSON")


if __name__ == "__main__":
    cli()
