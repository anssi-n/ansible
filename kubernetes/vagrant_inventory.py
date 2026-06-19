#!/usr/bin/env python3

"""
Returns inventory based on running VirtualBox VMs

Requires:
    - VirtualBox Guest Additions on VMs
    - vagrant vbguest plugin is installed (vagrant plugin install vagrant-vbguest)

CLI arguments:

- --list: Return the complete inventory (all groups and hosts).
- --host <hostname>: Return variables for a specific host.
"""

import json
import sys
import argparse
from typing import Dict, Any
import subprocess
from collections import defaultdict
from pathlib import Path
import re

class VMInfoError(BaseException):
    pass

def get_vm_info() -> Dict[str,tuple[str,str]]:
    script = """
        for vm in $(VBoxManage list runningvms | awk '{print $1}' | tr -d '"'); do
            VBoxManage guestcontrol "$vm" run --exe "/bin/bash" \
              --username vagrant --password vagrant -- -c '
                HOST=$(hostname)
                IP=$(ip -4 addr show eth1 2>/dev/null | grep -oP "(?<=inet\\s)\\d+(\\.\\d+){3}" | head -n1)
                echo "$HOST $IP"
              ' 2>/dev/null | tail -n 2
        done
    """

    try:
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            check=True
        )

        if result.stderr:
            raise VMInfoError(result.stderr)

        groups = defaultdict(list)

        for line in result.stdout.split("\n"):
            if line:
                hostname, ip = line.split()
                if host_index := re.findall(r"^([a-z0-9\-]+)-(\d+)$",hostname.strip()):
                    group_name, index = host_index[0]
                    groups[group_name].append((hostname.strip(),ip.strip()))
                else:
                    groups[hostname.strip()].append((hostname.strip(),ip.strip()))

        return groups

    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(e.stderr)


def get_inventory() -> Dict[str, Any]:

    vms = get_vm_info()

    inventory = {
                "_meta": {
                    "hostvars": {}
                },
                "control_plane_nodes": {
                    "hosts": []
                },
                "worker_nodes": {
                    "hosts": []
                },
                "lb_node": {
                    "hosts": []
                },
                "k8s_cluster": {
                    "children": [
                        "control_plane_nodes",
                        "worker_nodes"
                    ]
                },
                "all": {
                    "children": [
                        "ungrouped",
                        "lb_node",
                        "etcd_nodes",
                        "k8s_cluster"
                    ]
                },
            }

    for category, nodes in vms.items():
        for node, ip in nodes:
            if "lb" in category:
                inventory["lb_node"]["hosts"].append(node)
            elif "control" in category:
                inventory["control_plane_nodes"]["hosts"].append(node)
            elif "worker" in category:
                inventory["worker_nodes"]["hosts"].append(node)
            else:
                print(f"Warning: Unknown node category {category} with nodes {nodes}!")

            inventory["_meta"]["hostvars"][node] = {"ansible_host": ip,
                                                    "ansible_python_interpreter": "/usr/bin/python3.10",
                                                    "ansible_ssh_private_key_file": "~/.vagrant.d/insecure_private_key",
                                                    "ansible_user": "vagrant"}

    return inventory

def get_host_vars(hostname: str) -> Dict[str, Any]:

    inv = get_inventory()
    return inv["_meta"]["hostvars"].get(hostname, {})


def main():

    parser = argparse.ArgumentParser(description="Ansible Dynamic Inventory")
    parser.add_argument('--list', action='store_true', help='Return complete inventory')
    parser.add_argument('--host', help='Return variables for a specific host')
    args = parser.parse_args()

    try:
        if args.list:
            # Return full inventory
            inventory = get_inventory()
            print(json.dumps(inventory, indent=2))

        elif args.host:
            # Return variables for a specific host
            host_vars = get_host_vars(args.host)
            print(json.dumps(host_vars, indent=2))

        else:
            # No arguments: default to full inventory (some versions expect this)
            inventory = get_inventory()
            print(json.dumps(inventory, indent=2))

    except Exception as e:
        # Always handle errors gracefully
        print(json.dumps({"_error": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
