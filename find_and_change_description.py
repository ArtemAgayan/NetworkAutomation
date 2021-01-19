# Input data.
# Imagine that you are a network engineer and you are responsible for a large DC Fabric or for dozens of edge devices.
# For now there are no interface descriptions consistency and for future improvements you want to fix this problem.
# For example: leaf interfaces connected to spines should have "TO-SPINE-" at the beginning of interface description and vice versa. 
# Or "UPLINK-", if we are talking about ports on edge devices connected to providers.
# To simplify the task, we will assume that the existing description suits us and we only need to add "TO-SPINE-" or "UPLINK-" before them.
# And one important question: why, in principle, do we need to modify existing descriptions?
# For example, to add some flexibility to a Network Monitoring System(will appear the ability to group all uplink traffic, if NMS supports such feature). 
# Or to have standardization in description for automation goals.
# Anyway to achive this, a Python script can be used.
# I have split this code in two parts:
# first is just to gather descriptions information from devices - devices_output = find_ip(devices, "show interfaces Port-Channel 1-4 description", limit = 2).
# second is to modify descriptions and to change them on devices - a code that will execute after above line.
# In my example Port-Channel interfaces are connected to providers, so that's why I use above command(on some devices only one ISP link can exists, on others - up to four)
# Also a yaml file should be created, consisted of below parameters:
# - device_type: arista_eos
#   ip: edge-switch-1
#   username: <username>
#   password: <password>
# - device_type: arista_eos
#   ip: edge-switch-2
#   username: <username>
#   password: <password>
# ...etc...

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler
from pprint import pprint
import re
from itertools import repeat
import yaml

def send_show_command(device, command):
    '''
    Sends show command to device and also gather a current network device prompt(hostname variable will be parsed in find_ip function later).
    '''
    with ConnectHandler(**device) as ssh:
        output = ssh.send_command(command)
        hostname = ssh.find_prompt()
        total = f'{hostname}{command}\n{output}'
    return total

def find_ip(devices, command, limit):
    '''
    Executes the send_show_command function on all devices from yaml file, parse an output and return a list of nested dictionaries with switch hostname as key and interface and description as value.
    Variables:
    result - is the result of execution the first function on all devices. 
    interface/description/hostname _regexes - are regexes to parse this values.
    end_list - list of nested dictionaries from all devices with switch hostname as key and interface and description as value. 
    switch - output from one particular switch.
    interfaces/descriptions/hostnames - iterators for respective values from one particular switch.
    list_of_interfaces/list_of_descriptions - lists of interfaces and descriptions values from one particular switch.
    end_result - nested dictionary from one particular switch with switch hostname as key and interface and description as value.
    interface/descr - one particular interface/interface description from one particular switch.
    hostname - switch hostname.
    Arista uses below type of "show interfaces description" command output(Status values can be "up"/"down"/"admin down" and Protocol - "up"/"down"):
    Interface                      Status         Protocol           Description
    Po1                            up             up                 ISP1-<channel-id>
    '''
    with ThreadPoolExecutor(max_workers = limit) as executor:
        result = executor.map(send_show_command, devices, repeat(command))
        interface_regex = (r'Po(?P<interface>\d+)\s+')
        description_regex = (r'(?P<proto>up|down)\s+(?P<descr>\S+\s\S+)')
        hostname_regex = (r'(?P<hostname>\S+)#')
        end_list = []
        for switch in result:
            interfaces = re.finditer(interface_regex, switch)
            descriptions = re.finditer(description_regex, switch)
            hostnames = re.finditer(hostname_regex, switch)
            list_of_interfaces = []
            list_of_descriptions = []
            end_result = {}
            for match in interfaces:
                interface = match.group().strip()
                list_of_interfaces.append(interface)
            for match in descriptions:
                descr = match.group(2)
                list_of_descriptions.append(descr)
            int_descr_dict = dict(zip(list_of_interfaces,list_of_descriptions))
            for match in hostnames:
                hostname = match.group().strip("#")
            end_result[hostname] = int_descr_dict
            end_list.append(end_result)
        return end_list     

def send_config_commands(device, commands):
    '''
    Sends config command to device.
    '''
    with ConnectHandler(**device) as ssh:
        ssh.enable()
        result = ssh.send_config_set(commands)
    return result

if __name__ == "__main__":
    with open('devices.yaml') as f:
        devices = yaml.safe_load(f)
        devices_output = find_ip(devices, "show interfaces Port-Channel 1-4 description", limit = 2)
        pprint(devices_output)
        # The result of this part of code should be something like this:
        # [{'edge-switch-1': {'Po1': 'ISP1',
        #                     'Po2': 'ISP2',
        #                     'Po3': 'ISP3'}},
        #  {'edge-switch-2': {'Po1': 'ISP1',
        #                     'Po2': 'ISP2',
        #                     'Po3': 'ISP3'}}]
        #
        # After this second part of code will ecexute. The idea is to extract from above output lists of command, which will be send to appripriate switches.   
        # Variables:
        # interfaces/descriptions - lists of interfaces and descriptions respectively.
        # device - nested dictionary from one particular switch with switch hostname as key and interface and description as value.
        # commands - list of commands intended for one particular switch.
        # interface - string in "interface Po1" format.
        # description - string in "description UPLINK-ISP1" format.
        # command - pair of commands to enter interface mode and add the modified description.
        # switch - a set of settings for ssh connection for one particular switch.
        interfaces = []
        descriptions = []
        for device in devices_output:
            commands = []
            for hostname, int_descr_dict in device.items():
                for interface, description in int_descr_dict.items():
                    interface = str("interface ") + interface
                    description = str("description ") + "UPLINK-" + description
                    command = [interface] + [description]
                    commands.extend(command)
        for switch in devices:
            pprint(send_config_commands(switch, commands))
            
            # The result of this part of code should be something like this:
            # ('config term\n'
            #  'edge-switch-1(config)#interface Po1\n'
            #  'edge-switch-1(config-if-Po1)#description UPLINK-ISP1\n'
            #  'edge-switch-1(config-if-Po1)#interface Po2\n'
            #  'edge-switch-1(config-if-Po2)#description UPLINK-ISP2\n'
            #  'edge-switch-1(config-if-Po2)#interface Po3\n'
            #  'edge-switch-1(config-if-Po3)#description UPLINK-ISP3\n'
            #  'edge-switch-1(config-if-Po3)#end\n'
            #  'edge-switch-1#')
            # ('config term\n'
            #  'edge-switch-2(config)#interface Po1\n'
            #  'edge-switch-2(config-if-Po1)#description UPLINK-ISP1\n'
            #  'edge-switch-2(config-if-Po1)#interface Po2\n'
            #  'edge-switch-2(config-if-Po2)#description UPLINK-ISP2\n'
            #  'edge-switch-2(config-if-Po2)#interface Po3\n'
            #  'edge-switch-2(config-if-Po3)#description UPLINK-ISP3\n'
            #  'edge-switch-2(config-if-Po3)#end\n'
            #  'edge-switch-2#')
            
# This script can be used for other purposes as well. For example to gather an information about inactive bgp peers and than to delete them. 
# Or only the first part of this code can be implemented, for information gathering purposes.
