import datetime
import os
import sys
import ipaddress
import logging
import meraki
import pynetbox

# Either input your API key below by uncommenting line 10 and changing line 16 to api_key=API_KEY,
# or set an environment variable (preferred) to define your API key. The former is insecure and not recommended.
# For example, in Linux/macOS:  export MERAKI_DASHBOARD_API_KEY=093b24e85df15a3e66f1fc359f4c48493eaa1b73
# API_KEY = '093b24e85df15a3e66f1fc359f4c48493eaa1b73'


class MerakiNetbox:
    def __init__(self):

        self.discovered_tag = 'discovered'
        self.discover_network_clients_tag = 'discover-clients'
        self.discover_expiration = 7

        # Initialize logging
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
        self.logging = logging.getLogger()

        # Initialize Netbox
        if "NETBOX_URL" in os.environ:
            self.nb_url = os.getenv("NETBOX_URL")
        else:
            logging.error("Environmnet variable NETBOX_URL must be set")
            sys.exit(1)

        if "NETBOX_TOKEN" in os.environ:
            self.nb_token = os.getenv("NETBOX_TOKEN")
        else:
            logging.error("Environmnet variable NETBOX_TOKEN must be set")
            sys.exit(1)

        self.nb = pynetbox.api(url=self.nb_url, token=self.nb_token)
        self.nb_prefixes = self.nb.ipam.prefixes.all()
        self.nb_ip_addresses = self.nb.ipam.ip_addresses.all()

        # Inititalize Meraki
        if "MERAKI_ORG_ID" in os.environ:
            self.org_id = os.getenv("MERAKI_ORG_ID")
        else:
            logging.error("Environmnet variable MERAKI_ORG_ID must be set")
            sys.exit(1)

        if "MERAKI_TIMESPAN" in os.environ:
            self.timespan = os.getenv("MERAKI_TIMESPAN")
        else:
            self.timespan = 60 * 60 * 1

        self.meraki_time_format = '%Y-%m-%dT%XZ'

        self.dashboard = meraki.DashboardAPI(api_key='',
                                             base_url='https://api.meraki.com/api/v1/',
                                             output_log=False,
                                             log_file_prefix=os.path.basename(__file__)[:-3],
                                             log_path='',
                                             print_console=False)

    def check_prefixes(self, ip_address):
        for prefix in self.nb_prefixes:
            if prefix.status.value == 'active' and (ipaddress.ip_address(ip_address) in ipaddress.ip_network(
                    prefix.prefix)):
                return prefix.prefix.split('/')[1]
        return None

    def check_ip_addresses(self, ip_address):
        for nb_ip_address in self.nb_ip_addresses:
            if ip_address in nb_ip_address.address:
                return nb_ip_address
        return None

    def is_discovered(self, nb_ip_address):
        for tag in nb_ip_address.tags:
            if tag.name == self.discovered_tag:
                return True
        return False

    def add_nb_ip_address(self, client, prefix):
        # pprint(client)
        address = client['ip'] + '/' + prefix
        last_seen = datetime.datetime.strptime(client['lastSeen'], '%Y-%m-%dT%XZ')
        custom_fields = {'last_seen': last_seen.strftime('%Y-%m-%d'), 'mac': client['mac']}
        nb_ip_address = self.check_ip_addresses(address)
        ## We need to add/update
        if nb_ip_address:
            self.logging.debug("Updating %s", address)
            update_dict = {'address': address, 'status': 'active', 'custom_fields': custom_fields}
            nb_ip_address.update(update_dict)
        else:
            self.logging.debug("Adding %s", address)
            description = ""
            if client['description']:
                description = client['description']
            try:
                self.nb.ipam.ip_addresses.create(address=address,
                                                 status="active",
                                                 description=description,
                                                 custom_fields=custom_fields,
                                                 tags=[{
                                                     'name': self.discovered_tag
                                                 }])
            except pynetbox.lib.query.RequestError as e:
                self.logging.error(e.error)

    def is_expired(self, nb_ip_address, days_to_expire):
        if 'last_seen' in nb_ip_address.custom_fields and 'last_seen':
            try:
                last_seen = datetime.datetime.strptime(nb_ip_address.custom_fields['last_seen'], '%Y-%m-%d')
            except Exception:
                return False
            time_since_seen = datetime.datetime.now() - last_seen
            if time_since_seen.days > days_to_expire:
                self.logging.debug("Record for %s has expired: last seen on %s", nb_ip_address, last_seen)
                return True

        # Either the record is not expired or we cannot determine if it is
        return False

    def expire_nb_ip_addresses(self):
        # We need to set to "reserved" or delete if the record was discovered
        for nb_ip_address in self.nb_ip_addresses:
            if str(nb_ip_address.status).lower() == 'active':
                if self.is_expired(nb_ip_address, self.discover_expiration):
                    if self.is_discovered(nb_ip_address):
                        self.logging.debug("Deleting %s", nb_ip_address)
                        try:
                            nb_ip_address.delete()
                        except Exception as e:
                            self.logging.info(e.error)
                    else:
                        self.logging.debug("Setting %s to 'reserved'", nb_ip_address)
                        update_dict = {'status': 'reserved'}
                        nb_ip_address.update(update_dict)

    def get_meraki_networks(self, org_id):
        try:
            networks = self.dashboard.organizations.getOrganizationNetworks(org_id)
        except meraki.APIError as e:
            self.logging.error('Meraki API error: %s', e)
            self.logging.error('status code = %s', e.status)
            self.logging.error('reason = %s', e.reason)
            self.logging.error('error = %s', e.message)
            sys.exit(1)
        except Exception as e:
            self.logging.error('some other error: %s', e)
            sys.exit(1)
        return networks

    def get_meraki_network_clients(self, network_id):
        try:
            # Get list of clients on network, filtering on self.timespan of last 14 days
            clients = self.dashboard.networks.getNetworkClients(network_id,
                                                                timespan=self.timespan,
                                                                perPage=1000,
                                                                total_pages='all')
        except meraki.APIError as e:
            self.logging.error('Meraki API error: %s', e)
            self.logging.error('status code = %s', e.status)
            self.logging.error('reason = %s', e.reason)
            self.logging.error('error = %s', e.message)
        except Exception as e:
            self.logging.error('some other error: %s', e)
        else:
            return clients
        return []

    def discover_meraki_clients(self):
        # Get list of networks in organization
        networks = self.get_meraki_networks(self.org_id)

        # Iterate through networks
        total = len(networks)
        counter = 1
        self.logging.debug('  - iterating through %s networks in organization %s', total, self.org_id)
        for net in networks:
            if self.discover_network_clients_tag in net["tags"]:
                self.logging.debug('Finding clients in network %s (%s of %s)', net["name"], counter, total)
                clients = self.get_meraki_network_clients(net["id"])
                for client in clients:
                    if client['ip']:
                        prefix = self.check_prefixes(client['ip'])
                        if prefix:
                            self.add_nb_ip_address(client, prefix)
