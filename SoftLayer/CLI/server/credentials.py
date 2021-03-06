"""List virtual server credentials."""
# :license: MIT, see LICENSE for more details.
import SoftLayer
from SoftLayer.CLI import environment
from SoftLayer.CLI import formatting

import click


@click.command()
@click.argument('identifier')
@environment.pass_env
def cli(env, identifier):
    """List virtual server credentials."""

    hardware = SoftLayer.HardwareManager(env.client)
    result = hardware.get_hardware(identifier)
    table = formatting.Table(['username', 'password'])
    for item in result['operatingSystem']['passwords']:
        table.add_row([item['username'], item['password']])
    return table
