#!/usr/bin/env python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: packet_ip_block

short_description: Using Packet.net, assign a block of IPs to a host

version_added: "2.6"

description:
    - "The Packet.net ansible module provides basic functionality for managing hosts, but ignores the elastic IP address assignment. This module addresses taht by allowing for address block request and allocation.  Cleanup is also possible."

options:
    type:
        description:
            - This defines either the global or public IPv4 type.  Currently, only public makes sense.
        required: false
        default:
            - public_ipv4
    comment:
        description:
            - A comment that can be passed to the IP create. Not currently used.
        required: false
    quantity:
        description:
            - CIDR block to assign, must be an integer and power of 2. 4,8,16,32 are reasonable.
        required: true
    facility:
        description:
            - The location where the block will be assigned. Should match the facility of the host.
        required: true
    hostname:
        description:
            - The hostname of the host to which the block will be attached.
        required: true
    auth_token:
        description:
            - The PACKET_AUTH_TOKEN from app.packet.net for the project.
        required: false
    project_id:
        description:
            - The PACKET_PROJECT_ID from app.packet.net.
        required: false
    state:
        description:
            - Create or delete the IP block.
        required: true
        default:
            - present

author:
    - Robert Starmer (@rstarmer)
'''

EXAMPLES = '''
# create a block and assign it. 
- name: Create and Assign an IP block
  packet_ip:
        "quantity": "8",
        "facility": "sjc1",
        "auth_token": "AUTH_TOKEN_FROM_PACKET_NET",
        "project_id": "PROJECT_ID_FROM_PACKET_NET",
        "hostname": "testhost.example.com",
        "state": "present"
'''

RETURN = '''
meta:
    description: The address data and ID for the newly assigned block
    type: object
'''

#!/usr/bin/env python
from ansible.module_utils.basic import *
import requests

def create_record(data):

    record = {
        'type': data['type'],
        'facility': data['facility'],
        'quantity': data['quantity'],
        'comments': data['comment']
    }
    
    headers = {
        'X-Auth-Token': data['auth_token'],
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    url="https://api.packet.net/projects/"+ data['project_id'] +"/ips"
    req=requests.post(url,json=record,headers=headers)
    contents=json.loads(req.content)

    if req.status_code == 201:
        record_created=True
        addr_address=contents['address']
        addr_cidr=contents['cidr']
        meta={
            'addr_id': contents['id'],
            'addr_address': addr_address,
            'addr_net': contents['network'],
            'addr_gw': contents['gateway'],
            'addr_cidr': addr_cidr
            }
        has_changed=False
    else:
        record_created=False
        has_changed=False
        meta={}
    
    if record_created is True:
        url="https://api.packet.net/projects/"+ data['project_id'] +"/devices"
        req=requests.get(url,headers=headers)
        contents=json.loads(req.content)
        if req.status_code == 200:
            meta={'device':contents['devices'],'data':data['hostname']}
            for device in contents['devices']:
                if data['hostname'] == device['hostname']:
                    url="https://api.packet.net/devices/" + device['id'] + "/ips"
                    request_addr= addr_address +'/'+ str(addr_cidr)
                    record={
                        'address':request_addr,
                        'manageable':'true'
                        }
                    req=requests.post(url,json=record,headers=headers)
                    if req.status_code == 201:
                        has_changed=True
                    else:
                        has_changed=False
                        meta={'result': 'unable to assign address'}
    return (has_changed, meta)

def delete_record(data):

    headers = {
        'X-Auth-Token': data['auth_token'],
        'Accept': 'application/json'
    }

    url="https://api.packet.net/projects/"+ data['project_id'] +"/ips"
    req=requests.get(url, headers=headers)
    contents=json.loads(req.content)
    for address in contents['ip_addresses']:
        if address['cidr'] is 56 or address['cidr'] is 25:
            pass
        else:
            url="https://api.packet.net/ips/"+ address['id']
            req=requests.delete(url, headers=headers)
            if req.status_code == 204:
                meta={ 'address': address['id'], 'result': 'deleted'}
                has_changed=True
            else:
                meta={'result': 'address not found'}
                has_changed=False
    return (has_changed, meta)


def main():
    fields = {
        "type": {"required": False, "default": "public_ipv4", "type": "str"},
        "comment": {"required": False, "type": "str"},
        "quantity": {"required": True, "type": "str"},
        "facility": {"required": True, "type": "str"},
        "hostname": {"required": True, "type": "str"},
        "auth_token": {"required": True, "type": "str"},
        "project_id": {"required": True, "type": "str"},
        "state": {"default": "present","choices": ['present', 'absent'],"type": 'str'}
    }

    choice_map = {
      "present": create_record,
      "absent": delete_record
    }

    module = AnsibleModule(argument_spec=fields)
    has_changed, result = choice_map.get(module.params['state'])(module.params)
    module.exit_json(changed=has_changed, meta=result)

if __name__ == '__main__':
    main()
