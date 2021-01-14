# How to simultaneously gather ip-addresses of inactive bgp peers from several Arista switches using Python.
# Firstly yaml file should be created, consisted of below parameters:
# - device_type: arista_eos
#   ip: 192.168.111.111
#   username: <username>
#   password: <password>
# - device_type: arista_eos
#   ip: 192.168.111.222
#   username: <username>
#   password: <password>
# ...etc...

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler
import re
from itertools import repeat
import yaml

def send_show_command(device, command):
    '''
    Allows to gather an output of "show ip bgp summary | exclude Estab" command with current network device prompt.
    '''
    with ConnectHandler(**device) as ssh:
        output = ssh.send_command(command)
        hostname = ssh.find_prompt()
        total = f'{hostname}{command}\n{output}'
    return total

with open('devices.yaml') as f:
    devices = yaml.safe_load(f)

def find_ip(devices, command, limit):
    '''
    Allows ho have a list of outputs from all switches.
    '''
    end_list = []
    with ThreadPoolExecutor(max_workers = limit) as executor:
        result = executor.map(send_show_command, devices, repeat(command))
    for switch_output in result:
        end_list.append(switch_output)
    return end_list

# Here the result of second function begins to parse. 
# Variables ip_addresses and hostnames are iterators from which values of devices hostnames and inactive bgp peers ip-addresses are extracted.
# Variable end_result is a dictionary with device hostname as key and list of inactive bgp peers ip-addresses as value.
if __name__ == "__main__":
    devices_output = find_ip(devices, "show ip bgp summary | exclude Estab", limit = 2)
    ip_regex = (r'\s+(?P<ip>(\d+\.){3}\d+)')
    hostname_regex = (r'(?P<hostname>\S+)#')
    for switch_output in devices_output:
        ip_addresses = re.finditer(ip_regex, switch_output)
        hostnames = re.finditer(hostname_regex, switch_output)
        end_result = {}
        list_of_ips = []
        for match in hostnames:
            hostname = match.group().strip("#")
        for match in ip_addresses:
            one_ip = match.group().strip()
            list_of_ips.append(one_ip)
        end_result[hostname] = list_of_ips
        print(end_result)
        
# The result should be something like this:
#  % ./find_ip.py  
# {'192.168.111.111': ['10.10.10.1', '20.20.20.1', '30.30.30.1', '40.40.40.1']}
# {'192.168.111.222': ['10.10.10.2', '20.20.20.2', '30.30.30.2', '40.40.40.2']}
# Then for example with jinja2 help and simple new python script or ansible playbook this peers can be deleted from devices.
