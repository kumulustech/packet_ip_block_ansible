An extension to the Packet ansible module
=========================================

A small extension to the Ansible packet module (shoudl eventually
be incorporated I'd guess), to support the allocation and assignment of
Packet elastic IP blocks.

I wrote this to support adding a block of addresses to an single node
gateway that supports "Floating IP" addresses for an IaaS model for
classes I run.

You will need the requests python module (shoudl already be installed if you have ansible installed), but you can load it with:

    pip install -r requirements.txt

Then, just drop the packet_ip.py module into the library/ directory next to your playbook(s), or add it to the master ansible library.

An example task:

    # create a block and assign it. 
    - name: Create and Assign an IP block
      packet_ip:
            "quantity": "8",
            "facility": "sjc1",
            "auth_token": "AUTH_TOKEN_FROM_PACKET_NET",
            "project_id": "PROJECT_ID_FROM_PACKET_NET",
            "hostname": "testhost.example.com",
            "state": "present"

More documentation in the module.

