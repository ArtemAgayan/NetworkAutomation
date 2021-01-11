# Input data.
# Imagine that in our network we have several dozen CentOS servers and several docker containers running on each server.
# There is a need to gather a firmware version of the particular application on certain container for each server and then compare them.
# It can be a challenge to log in on all devices, find a path to needed container, open a file where information about a firmware resides, find a particular  
# string among all information there, make a note and finally log out from device.
# Instead of doing all this actions a python script can be used.
# It takes about 6 seconds to execute all this steps on 25 servers.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import time
from concurrent.futures import ThreadPoolExecutor
import re

def gather_output(device):
# Allows to connect to one device and gather all information from a file which contains a firmware version value.
# <file_where_firmware_information_resides> is .txt file with dozens strings among which there is one with firmware version and it begins with "VERSION"
# I don't use password as credentials because I have key authentication on my servers.
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=device, username="name", port="22")
    ssh = client.invoke_shell()
    ssh.send("sudo su\n")
    time.sleep(1)
    ssh.send("cd /<path_to_needed_container>")
    time.sleep(1)
    ssh.send("cat <file_where_firmware_information_resides>")
    time.sleep(1)
    result = ssh.recv(1000).decode("utf-8")
    ssh.close()
    return result

def show_versions(servers_list, limit):
# Allows to connect to all devices from the list in parallel using the first function, parse only version values and make a dictionary with
# server hostname/ip address as key and firmware version as value.
    with ThreadPoolExecutor(max_workers = limit) as executor:
        result = executor.map(gather_output, servers_list)
        for server, output in zip(servers_list, result):
            data = {}
            match = re.search('VERSION=(\S+)', output)
            version = match.group()
            data[server] = version
            print(data)

if __name__ == "__main__":
    servers_list = ["hostname/ip address", "hostname/ip address", "hostname/ip address" ...]
    show_versions(servers_list, limit = 25)
    
# The result should be something like this:
# {'server1': 'VERSION=1.2.03'}
# {'server2': 'VERSION=1.2.04'}
# {'server3': 'VERSION=1.2.03'}
# {'server4': 'VERSION=1.2.02'}
# ...
