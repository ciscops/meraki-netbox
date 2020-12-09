import meraki_netbox
import datetime

if __name__ == '__main__':
    start_time = datetime.datetime.now()
    meraki_netbox.discover_meraki_clients()
    end_time = datetime.datetime.now()
    print(f'\nScript complete, total runtime {end_time - start_time}')