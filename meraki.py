import requests
import json

base_url = 'https://api.meraki.com/api/v0'
api_key = '6bec40cf957de430a6f1f2baa056b99a4fac9ea0'
headers = {'X-Cisco-Meraki-API-Key': f"{api_key}"}
org_id = '549236'
def_network_id = 'L_646829496481104109'

def get_networks():
    url = f'{base_url}/organizations/{org_id}/networks'

    network_list = requests.get(url, headers=headers).json()

    return network_list

def get_ssids(network_id):
    url = f"{base_url}/networks/{network_id}/ssids"

    ssid_list = requests.get(url, headers=headers).json()

    return ssid_list

def start_scanning():
    location_simulator = 'http://dev.web.local:5002/startscan'
    data = {"post_server": "http://dev.student.local:5005/location"}

    start_scan = requests.post(location_simulator, data=data).text

    return start_scan

def get_location():
    getlocation_url = 'http://dev.student.local:5005/getlocation'
    
    location_data = requests.get(getlocation_url).json()

    return location_data
