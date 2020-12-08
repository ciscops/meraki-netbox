import datetime
import os
from pprint import pprint
import ipaddress
import meraki
import pynetbox

# Either input your API key below by uncommenting line 10 and changing line 16 to api_key=API_KEY,
# or set an environment variable (preferred) to define your API key. The former is insecure and not recommended.
# For example, in Linux/macOS:  export MERAKI_DASHBOARD_API_KEY=093b24e85df15a3e66f1fc359f4c48493eaa1b73
# API_KEY = '093b24e85df15a3e66f1fc359f4c48493eaa1b73'

days_to_expire = 0
discovered_tag = 'discovered'
meraki_time_format = '%Y-%m-%dT%XZ'


def check_prefixes(ip_address):
    for prefix in nb_prefixes:
        if prefix.status.value == 'active' and (ipaddress.ip_address(ip_address) in ipaddress.ip_network(
                prefix.prefix)):
            print(prefix.prefix)
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
                # expire_time = datetime.timedelta(days=days_to_expire)
                nb_ip_address = check_ip_addresses(address)
                if datetime.datetime.now() - last_seen < datetime.timedelta(days_to_expire):
                    pprint(client)
                    ## We need to add/update
                    if nb_ip_address:
                        print(f"Updating {address}")
                        update_dict = {'address': address, 'status': 'active'}
                        nb_ip_address.update(update_dict)
                    else:
                        print(f"Adding {address}")
                        description = ""
                        if client['description']:
                            description = client['description']
                        try:
                            nb.ipam.ip_addresses.create(address=address,
                                                        status="active",
                                                        description=description,
                                                        custom_fields={
                                                            'last_seen': last_seen.strftime('%Y-%m-%d'),
                                                            'mac': client['mac']
                                                        },
                                                        tags=[{
                                                            'name': discovered_tag
                                                        }])
                        except pynetbox.lib.query.RequestError as e:
                            print(e.error)
                else:
                    ## We need to set to "reserved" or delete if the record was discovered
                    if nb_ip_address:
                        if is_discovered(nb_ip_address):
                            print(f"Deleting {address}")
                            try:
                                nb_ip_address.delete()
                            except Exception as e:
                                print(e.error)
                        else:
                            print(f"Setting to 'reserved': {address}")
                            update_dict = {'address': address, 'status': 'reserved'}
                            nb_ip_address.update(update_dict)


def main():
    # Instantiate a Meraki dashboard API session
    dashboard = meraki.DashboardAPI(api_key='',
                                    base_url='https://api-mp.meraki.com/api/v1/',
                                    output_log=True,
                                    log_file_prefix=os.path.basename(__file__)[:-3],
                                    log_path='',
                                    print_console=False)
    org_id = "572081"

    # Get list of networks in organization
    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
    except meraki.APIError as e:
        print(f'Meraki API error: {e}')
        print(f'status code = {e.status}')
        print(f'reason = {e.reason}')
        print(f'error = {e.message}')
        return
    except Exception as e:
        print(f'some other error: {e}')
        return

    # Iterate through networks
    total = len(networks)
    counter = 1
    print(f'  - iterating through {total} networks in organization {org_id}')
    for net in networks:
        print(f'Finding clients in network {net["name"]} ({counter} of {total})')
        try:
            # Get list of clients on network, filtering on timespan of last 14 days
            clients = dashboard.networks.getNetworkClients(net['id'],
                                                           timespan=60 * 60 * 24 * 1,
                                                           perPage=1000,
                                                           total_pages='all')
        except meraki.APIError as e:
            print(f'Meraki API error: {e}')
            print(f'status code = {e.status}')
            print(f'reason = {e.reason}')
            print(f'error = {e.message}')
        except Exception as e:
            print(f'some other error: {e}')
        else:
            if clients:
                process_meraki_clients(clients)


if __name__ == '__main__':
    nb_url = os.getenv("NETBOX_URL")
    nb_token = os.getenv("NETBOX_TOKEN")

    nb = pynetbox.api(url=nb_url, token=nb_token)
    nb_prefixes = nb.ipam.prefixes.all()
    nb_ip_addresses = nb.ipam.ip_addresses.all()
    start_time = datetime.datetime.now()
    main()
    end_time = datetime.datetime.now()
    print(f'\nScript complete, total runtime {end_time - start_time}')
