#!/usr/bin/env python
# -*- coding: utf8 -*-
import logging

import click

from .cmds.processor import Project

# logging.getLogger().addHandler(logging.StreamHandler())
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def enableVerbose():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG)


@click.group()
def cli1():
    pass


@cli1.command()
@click.option('--url', '-u', default=None, help='URL of the Yandex.Disk public resource')
@click.option('--output', '-o', default=None, help='Output dir')
@click.option('--filename', '-f', default=None, help='Output filename')
@click.option('--metadata', '-m', is_flag=True, help='Extract and save metadata')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output. Print additional info')
def full(url, output, filename, metadata, verbose):
    """Full copy of public resource files"""
    if verbose:
        enableVerbose()
    if url is None:
        print('Public resource URL required')
        return
    acmd = Project()
    acmd.full(url, output, filename, metadata)
    pass


@click.group()
def cli2():
    pass


@cli2.command()
@click.option('--url', '-u', default=None, help='URL of the public resource to process')
@click.option('--output', '-o', default=None, help='Output path')
@click.option('--update', '-u', is_flag=True, help='Update only')
@click.option('--nofiles', '-n', is_flag=True, help='Files not stored, only metadata collected')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output. Print additional info')
def sync(url, output, update, nofiles, verbose):
    """Sync public resource files"""
    if verbose:
        enableVerbose()
    if url is None:
        print('Public resource URL required')
        return
    if output is None:
        output = url.rsplit('/d/', 1)[-1]
    acmd = Project()
    acmd.sync(url, output, update, nofiles)
    pass


cli = click.CommandCollection(sources=[cli1, cli2])

# if __name__ == '__main__':
#    cli()
