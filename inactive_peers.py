# How to collect information about bgp sessions which are inactive more then one week from one Arista device using Python.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from netmiko import ConnectHandler
from pprint import pprint
import re

device = input('Enter device ip-address or hostname: ')

def send_show_command(device, command):
    with ConnectHandler(**device) as ssh:
        output = ssh.send_command(command)
    return output

if __name__ == "__main__":
    device = {
        "device_type": "arista_eos",
        "ip": device,
        "username": "username",
        "password": "password",
    }
    output = send_show_command(device, "sh ip bgp summary | exclude Estab")
    regex = (r'(?P<description>.*?)\s+(?P<ip>\S+)\s+\d\s+(?P<as>\S+)(?:\s+\d+\s+){4}(?P<uptime>\S+)\s+(?P<state>\S+)')
    # Arista uses below type of "show ip bgp summary" command output:
    # Description              Neighbor         V  AS           MsgRcvd   MsgSent  InQ OutQ  Up/Down State   PfxRcd PfxAcc
    # BGP-PEER                 12.34.56.78      4  12345              0         0    0    0   10d00h Idle(Admin)         
    result = re.finditer(regex, output)
    pprint('-'*45)
    for match in result:
        uptime = match['uptime']
        if ":" in uptime:
            pass
        else:
            days, hours = uptime.split('d')
            if int(days) >= 7:
                pprint(match.groupdict(), sort_dicts=False)
                pprint('-'*45)


# The result should be something like this:
#  % ./inactive_peers.py  
# Enter device ip-address or hostname: test-switch
# '---------------------------------------------'
# {'description': '  BGP-PEER',
#  'ip': '12.34.56.78',
#  'as': '12345',
#  'uptime': '10d00h',
#  'state': 'Idle(Admin)'}
# '---------------------------------------------'
# {'description': '  BGP-PEERt',
#  'ip': '87.65.43.21',
#  'as': '54321',
#  'uptime': '10d10h',
#  'state': 'Active'}
# '---------------------------------------------'
