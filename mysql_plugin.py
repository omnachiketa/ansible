#!/usr/bin/python3

"""
mysql_plugin.py - retrieve inventory from the MySQL database

Author:
  Lohit Dutta <lohit.dutta@goto.com>

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
      mysql_user:
        description: MySQL user name
        required: true
      mysql_pass:
        description: MySQL user password
        required: true
      mysql_server:
        description: MySQL database server name
        required: true
      mysql_db:
        description: MySQL database name
        required: true
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
        self.connection = mysql.connect(
            host=self.mysql_host,
            user=self.mysql_user,
            password=self.mysql_pass,
            database=self.mysql_db
        )
        cursor = self.connection.cursor()
        cursor.execute(self.mysql_query)
        db_records = cursor.fetchall()
        cursor.close()
        self.connection.close()
        return db_records

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

    def execute_query(self,mysql_query, data=None):
        cursor = self.connection.cursor()
        if data:
            cursor.execute(mysql_query, data)
        else:
            cursor.execute(mysql_query)
        result = cursor.fetchall()
        cursor.close()
        self.connection.commit()
        return result

    def _populate(self):
        '''Connect to mysql database'''

        '''Return the hosts and groups'''
        self.myinventory = self._get_mysql_data()
        for hostname,attributes in self.myinventory.items():
          for key in ['hostgroup', 'domain', 'env']: 
            gname = self.inventory.add_group(attributes[key])
            self.inventory.add_host(host=hostname, group=gname)
