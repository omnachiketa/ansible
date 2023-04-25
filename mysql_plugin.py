#!/usr/bin/python3
"""
mysql_plugin.py - retrieve inventory from the database

Author:
  Lohit Dutta <lohit.dutta@goto.com> [DOIS-CORE-SERVICES]

Copyright:
  2023, GoTo Technologies, Inc
"""

DOCUMENTATION = r'''
    name: mysql_plugin
    plugin_type: inventory
    short_description: Returns ansible inventory from mysql database
    description: Returns Ansible inventory from mysql database
    options:
      plugin:
          description: Name of the plugin
          required: true
          choices: ['mysql_plugin']
      query_string:
        description: details of the objects to find
        required: true
'''

from ansible.plugins.inventory import BaseInventoryPlugin
import mysql.connector as mysql 
from ansible.errors import AnsibleError, AnsibleParserError
import os
__metaclass__ = type



class InventoryModule(BaseInventoryPlugin):
    NAME = 'mysql_plugin'

    def _get_mysql_data(self):
        """Run a SQL query."""
        with mysql.connect(user=self.mysql_user, password=self.mysql_pass, host=self.mysql_host,database=self.mysql_db) as connection:
          cursor = connection.cursor()
          cursor.execute("SELECT * FROM inventory")
          db_records = cursor.fetchall()
          # Select query to retrive the column names for the inventory table;
          cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = N'inventory' ORDER BY ORDINAL_POSITION")
          keys = list(sum(cursor.fetchall(), ())) #Converting the SQL output to a list() format;
          extra_keys = ['hostname','uuid','provision_status','creation_time']
          inventory_data = {}
          if db_records:
              for record in db_records:
                values = list(record)  #Converting the SQL output to a list() format;
                host_attributes = {keys[i]:values[i] for i in range(len(keys))} # Creating an output{} dictionary to print the output in a Key value format;
                hostname = host_attributes['hostname']
                for k in extra_keys:
                  del host_attributes[k]
                inventory_data[hostname] = host_attributes
              return inventory_data
    
    def verify_file(self, path):
        '''Return true/false if this is a 
        valid file for this plugin to consume
        '''
        valid = False
        if super(InventoryModule, self).verify_file(path):
            #base class verifies that file exists 
            #and is readable by current user
            if path.endswith(('mysql_plugin.yaml',
                              'mysql_plugin.yml')):
                valid = True
        return valid

    def _populate(self):
        '''Connect to mysql database'''

        '''Return the hosts and groups'''
        self.myinventory = self._get_mysql_data()
        for hostname,attributes in self.myinventory.items():
            gname = self.inventory.add_group(attributes['hostgroup'])
            self.inventory.add_host(host=hostname, group=gname)

    def parse(self, inventory, loader, path, cache):
        '''Return dynamic inventory from source '''
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        try:
            self.mysql_user = 'ansibleawx'
            self.mysql_pass = 'PLHhrVTvhp6o6Y'
            self.mysql_host = 'ansibleinventory.c3i8ftiagcsi.us-east-1.rds.amazonaws.com'
            self.mysql_port = '3306'
            self.mysql_db = 'ansible' 
            self.mysql_query = self.get_option('query_string')
        except Exception as e:
            raise AnsibleParserError(
                'All correct options required: {}'.format(e))
        self._populate()
