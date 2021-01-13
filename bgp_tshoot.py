# Input data.
# You receive the alert message from Network Monitoring System that on certain switch or router one particular bgp session was down. 
# Instead of logging to this box and gathering all information manually, Python script can be used which will collect some basic information.
# This script is intended for Arista switches and checks several things:
# - bgp state, the output is parsed for better perceptions;
# - log messages related to problem bgp-peer;
# - result of ping command;
# - tcp dump output of packets destined to peer.
# For convenience before execution script will ask ip-addresses of switch and ip-address of bgp-peer, so there is no need to go to .py file and specify this values every time.
# I intentionally made a dedicated function for each command to divide outputs via dashes, I realize that this is not so elegant decision.
# This is just an example and of course some other things can be checked as well.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from netmiko import ConnectHandler
from pprint import pprint
import re

device = input('Enter device ip-address or hostname: ')
bgp_neighbor = input('Enter bgp_neighbor ip-address: ')

def connect(device):
    ‘’’
    Allows to log in to switch
    ‘’’
    ssh = ConnectHandler(**device)
    return ssh

def parse_bgp(command):
    ‘’’
    Allows to gather and parse some bgp summary information
    Arista uses below type of "show ip bgp summary" command output:
    Description              Neighbor         V  AS           MsgRcvd   MsgSent  InQ OutQ  Up/Down State   PfxRcd PfxAcc
    BGP-PEER                 12.34.56.78      4  12345              0         0    0    0   10d00h Active         
    ‘’’
    result = []
    regex = (r'(?P<description>.*?)\s+(?P<ip>\S+)\s+\d\s+(?P<as>\S+)(?:\s+\d+\s+){4}(?P<uptime>\S+)\s+(?P<state>\S+)')
    output = ssh.send_command(command)
    match = re.search(regex,output)
    result = match.groupdict()
    return result

def log_bgp(sh_log_command):
    log_output = ssh.send_command(sh_log_command)
    return log_output

def ping_check(ping_command):
    ping_output = ssh.send_command(ping_command)
    return ping_output

def tcp_dump(tcp_dump_command):
    dump_output = ssh.send_command_timing(tcp_dump_command)
    return dump_output

if __name__ == "__main__":
    device = {
        "device_type": "arista_eos",
        "ip": device,
        "username": "username",
        "password": "password",
    }

    ssh = connect(device)
    pprint('-'*200)
    pprint(parse_bgp("show ip bgp summary | in " '{}'.format(bgp_neighbor)),sort_dicts=False)
    pprint('-'*200)
    print(log_bgp("show logging | in " '{}'.format(bgp_neighbor)))
    pprint('-'*200)
    pprint(ping_check("ping " '{}'.format(bgp_neighbor)))
    pprint('-'*200)
    print(tcp_dump("tcpdump packet-count 20 filter port 179 and host " '{}'.format(bgp_neighbor)))
    pprint('-'*200)
    
    
# The result should be something like this:
# (I know that despite bgp session was hard reset, in tcp dump we can see ACK packet, this because I haven't bgp neighbors for testing and haven't time for 
# making lab, so please excuse me for this. I just add here the output of dump from another working neighbor for better understanding.)
#
# % ./bgp_tshoot.py   
# Enter device ip-address or hostname: test-switch
# Enter bgp_neighbor ip-address: 12.34.56.78
# '--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------'
# {'description': '  BGP-PEER ',
#  'ip': '12.34.56.78',
#  'as': ‘12345’,
#  'uptime': '10d00h',
#  'state': 'Active'}
# '--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------'
# 1970-01-01T00:00:01.336068+00:00 test-switch ConfigAgent: %BGP-5-PEER_CLEAR: BGP peering for neighbor 12.34.56.78 (vrf test) was hard reset by admin on vty7 (192.168.222.222)
# '--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------'
# ('PING 12.34.56.78 (12.34.56.78) 72(100) bytes of data.\n'
#  '80 bytes from 12.34.56.78: icmp_seq=1 ttl=62 time=0.137 ms\n'
#  '80 bytes from 12.34.56.78: icmp_seq=2 ttl=62 time=0.093 ms\n'
#  '80 bytes from 12.34.56.78: icmp_seq=3 ttl=62 time=0.081 ms\n'
#  '80 bytes from 12.34.56.78: icmp_seq=4 ttl=62 time=0.083 ms\n'
#  '80 bytes from 12.34.56.78: icmp_seq=5 ttl=62 time=0.082 ms\n'
#  '\n'
#  '--- 12.34.56.78 ping statistics ---\n'
#  '5 packets transmitted, 5 received, 0% packet loss, time 0ms\n'
#  'rtt min/avg/max/mdev = 0.081/0.095/0.137/0.022 ms, ipg/ewma 0.116/0.115 ms')
# '--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------'
# tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
# listening on fabric, link-type EN10MB (Ethernet), capture size 262144 bytes
# 00:00:01.543715 ab:cd:ef:12:34:56 > 12:34:56:78:90:ab, ethertype 802.1Q (0x8100), length 70: vlan 777, p 6, ethertype IPv4, 12.34.56.78.43210 > 10.1010.10.bgp: Flags [.], ack 333, win 111, options [nop,nop,TS val 48344322 ecr 846162414], length 0
# '--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------'
