import os
import logging
import datetime
import meraki_netbox

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.debug('new event received: '+ str(event))
    start_time = datetime.datetime.now()
    meraki_netbox.discover_meraki_clients()
    end_time = datetime.datetime.now()
    logger.debug(f'\nScript complete, total runtime {end_time - start_time}')