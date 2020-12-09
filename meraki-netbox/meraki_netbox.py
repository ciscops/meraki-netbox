import datetime
import os
from pprint import pprint
import ipaddress
import logging
import meraki
import pynetbox

# Either input your API key below by uncommenting line 10 and changing line 16 to api_key=API_KEY,
# or set an environment variable (preferred) to define your API key. The former is insecure and not recommended.
# For example, in Linux/macOS:  export MERAKI_DASHBOARD_API_KEY=093b24e85df15a3e66f1fc359f4c48493eaa1b73
# API_KEY = '093b24e85df15a3e66f1fc359f4c48493eaa1b73'

days_to_expire = 3
# The window to evaluate in seconds
timespan = 60 * 60 * 2
discovered_tag = 'discovered'
discover_network_clients_tag = 'discover-clients'
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

meraki_time_format = '%Y-%m-%dT%XZ'
nb_url = os.getenv("NETBOX_URL")
nb_token = os.getenv("NETBOX_TOKEN")
org_id = os.getenv("MERAKI_ORG_ID")
nb = pynetbox.api(url=nb_url, token=nb_token)
nb_prefixes = nb.ipam.prefixes.all()
nb_ip_addresses = nb.ipam.ip_addresses.all()


def check_prefixes(ip_address):
    for prefix in nb_prefixes:
        if prefix.status.value == 'active' and (ipaddress.ip_address(ip_address) in ipaddress.ip_network(
                prefix.prefix)):
            return prefix.prefix.split('/')[1]
    return None


def check_ip_addresses(ip_address):
    for nb_ip_address in nb_ip_addresses:
        if ip_address in nb_ip_address.address:
            return nb_ip_address
    return None


def is_discovered(nb_ip_address):
    for tag in nb_ip_address.tags:
        if tag.name == discovered_tag:
            return True
    return False


def process_meraki_clients(clients):
    for client in clients:
        # pprint(client)
        if client['ip']:
            prefix = check_prefixes(client['ip'])
            if prefix:
                # pprint(client)
                address = client['ip'] + '/' + prefix
                last_seen = datetime.datetime.strptime(client['lastSeen'], '%Y-%m-%dT%XZ')
                custom_fields = {'last_seen': last_seen.strftime('%Y-%m-%d'), 'mac': client['mac']}
                nb_ip_address = check_ip_addresses(address)
                logging.debug(f"{last_seen}")
                ## We need to add/update
                if nb_ip_address:
                    logging.debug(f"Updating {address}")
                    update_dict = {'address': address, 'status': 'active', 'custom_fields': custom_fields}
                    nb_ip_address.update(update_dict)
                else:
                    logging.debug(f"Adding {address}")
                    description = ""
                    if client['description']:
                        description = client['description']
                    try:
                        nb.ipam.ip_addresses.create(address=address,
                                                    status="active",
                                                    description=description,
                                                    custom_fields=custom_fields,
                                                    tags=[{
                                                        'name': discovered_tag
                                                    }])
                    except pynetbox.lib.query.RequestError as e:
                        logging.error(e.error)

                    ## We need to set to "reserved" or delete if the record was discovered
                    # if nb_ip_address:
                    #     if is_discovered(nb_ip_address):
                    #         logging.debug(f"Deleting {address}")
                    #         try:
                    #             nb_ip_address.delete()
                    #         except Exception as e:
                    #             logging.error(e.error)
                    #     else:
                    #         logging.debug(f"Setting to 'reserved': {address}")
                    #         update_dict = {'address': address, 'status': 'reserved', 'custom_fields': custom_fields}
                    #         nb_ip_address.update(update_dict)


def discover_meraki_clients():

    # Instantiate a Meraki dashboard API session
    dashboard = meraki.DashboardAPI(api_key='',
                                    base_url='https://api-mp.meraki.com/api/v1/',
                                    output_log=False,
                                    log_file_prefix=os.path.basename(__file__)[:-3],
                                    log_path='',
                                    print_console=False)

    # Get list of networks in organization
    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
    except meraki.APIError as e:
        logging.error(f'Meraki API error: {e}')
        logging.error(f'status code = {e.status}')
        logging.error(f'reason = {e.reason}')
        logging.error(f'error = {e.message}')
        return
    except Exception as e:
        logging.error(f'some other error: {e}')
        return

    # Iterate through networks
    total = len(networks)
    counter = 1
    logging.debug(f'  - iterating through {total} networks in organization {org_id}')
    for net in networks:
        if discover_network_clients_tag in net["tags"]:
            logging.debug(f'Finding clients in network {net["name"]} ({counter} of {total})')
            try:
                # Get list of clients on network, filtering on timespan of last 14 days
                clients = dashboard.networks.getNetworkClients(net['id'],
                                                            timespan=timespan,
                                                            perPage=1000,
                                                            total_pages='all')
            except meraki.APIError as e:
                logging.error(f'Meraki API error: {e}')
                logging.error(f'status code = {e.status}')
                logging.error(f'reason = {e.reason}')
                logging.error(f'error = {e.message}')
            except Exception as e:
                logging.error(f'some other error: {e}')
            else:
                if clients:
                    process_meraki_clients(clients)
