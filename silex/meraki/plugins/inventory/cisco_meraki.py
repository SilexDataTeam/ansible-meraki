# Copyright (c) 2024 Silex Data Systems
# Apache 2.0

from __future__ import annotations

DOCUMENTATION = '''
    name: cisco_meraki
    version_added: "2.14"
    requirements:
        - meraki
    short_description: Uses Cisco Meraki API as an inventory source.
    description:
        - Get inventory hosts from Meraki API.
    notes:
        - If you want to set vars for the C(all) group inside the inventory file, the C(all) group must be the first entry in the file.
        - Enabled in configuration by default.
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    options:
      plugin:
        description: token that ensures this is a source file for the C(cisco_meraki) plugin.
        required: true
        choices: ['silex.meraki.cisco_meraki']
      meraki_base_url:
        description:
          - URL of the Meraki API
        default: https://api.meraki.com/api/v1
      meraki_api_key:
        description:
          - Token created for the Meraki API
        required: true
        env: MERAKI_DASHBOARD_API_KEY
      group_prefix:
        description:
          - Prefix for group names
        required: false
        default: net_meraki_
      group_parent:
        description:
          - Parent group for all other groups
        required: false
      want_organization:
        description:
          - Toggle, if trye the inventory will fetch the organization the network belongs to and create groupings for the same
        type: boolean
        default: true
'''

import meraki

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, to_safe_group_name, Constructable

class InventoryModule(BaseInventoryPlugin, Cacheable, Constructable):
    '''Host inventory parser for ansible using Cisco Meraki API as source'''

    NAME = 'silex.meraki.cisco_meraki'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.dashboard = None
        self.group_parent = None
        self.group_prefix = None

    def verify_file(self, path):
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('meraki.yaml', 'meraki.yml')):
                valid = True
            else:
                self.display.vvv('Skipping due to inventory source not ending in "meraki.yaml" nor "meraki.yml"')
        return valid

    def add_host(self, hostname, host_vars):
        self.inventory.add_host(hostname)

        for var_name, var_value in host_vars.items():
            self.inventory.set_variable(hostname, var_name, var_value)

        strict = self.get_option('strict')

        # Add variables created by the user's Jinja2 expressions to the host
        self._set_composite_vars(self.get_option('compose'), host_vars, hostname, strict=True)

        # Create user-defined groups using variables and Jinja2 conditionals
        self._add_host_to_composed_groups(self.get_option('groups'), host_vars, hostname, strict=strict)
        self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host_vars, hostname, strict=strict)

    def _populate(self):
        self.groups = dict()
        self.hosts = dict()
        self.group_parent = self.get_option('group_parent')
        self.group_prefix = self.get_option('group_prefix')
        self.want_organization = self.get_option('want_organization')

        # Create parent group (if defined)
        if self.group_parent:
            self.inventory.add_group(self.group_parent)

        orgs = self.dashboard.organizations.getOrganizations()

        for org in orgs:
            networks = self.dashboard.organizations.getOrganizationNetworks(org['id'])

            # Create a group for the organization if desired
            if self.want_organization:
                org_group_name = to_safe_group_name("{0}organization_{1}".format(self.group_prefix, org['name'].lower().replace(' ', '')))
                self.inventory.add_group(org_group_name)
                if self.group_parent:
                    self.inventory.add_child(self.group_parent, org_group_name)

            for network in networks:
                host_vars = {
                    'ansible_connection': 'local',
                    'id': network['id'],
                    'product_types': network['productTypes'],
                    'tags': network['tags'],
                    'time_zone': network['timeZone'],
                    'enrollment_string': network['enrollmentString'],
                    'notes': network['notes'],
                    'url': network['url'],
                    'org_id': org['id'],
                    'org_name': org['name']
                }
                self.add_host(network['name'], host_vars)

                if self.want_organization:
                    self.inventory.add_child(org_group_name, network['name'])

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        # Read config from file
        self._read_config_data(path)

        self.dashboard = meraki.DashboardAPI(suppress_logging=True)

        # Populate the inventory
        self._populate()
