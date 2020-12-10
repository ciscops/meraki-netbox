import os
import logging
import datetime
from meraki_netbox import MerakiNetbox

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.debug('new event received: %s', str(event))
    start_time = datetime.datetime.now()
    meraki_netbox = MerakiNetbox()
    meraki_netbox.discover_meraki_clients()
    end_time = datetime.datetime.now()
    logger.debug('Script complete, total runtime {%s - %s}', end_time, start_time)
