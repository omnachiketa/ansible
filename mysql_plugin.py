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
        # with mysql.connect(user=self.mysql_user, password=self.mysql_pass, host=self.mysql_host,database=self.mysql_db) as connection:
        cursor = self.connection.cursor()
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
            cursor.close()
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
        try:
            self.myinventory = self._get_mysql_data()
            for hostname,attributes in self.myinventory.items():
              for key in ['hostgroup', 'domain', 'env']: 
                gname = self.inventory.add_group(attributes[key])
                self.inventory.add_host(host=hostname, group=gname)
                variables = eval(str(attributes['var']))
                if variables:
                  for name, value in variables.items():
                    self.inventory.set_variable(hostname, name, value)
                query = f"SELECT v.name, p.value FROM parameters AS p JOIN categories AS c ON p.category_id = c.id JOIN variables AS v ON p.var_id = v.id WHERE c.type = %s AND c.description = %s"
                values = (key,attributes[key])
                result = self.execute_query(query,values)
                if result:
                  vars = {var[0]: var[1] for var in result}
                  for k,v in vars.items():
                    self.inventory.set_variable(hostname, k,v)
        except Exception as e:
            raise AnsibleParserError('DB data not able to papulate: {}'.format(e))
              
    def parse(self, inventory, loader, path, cache):
        '''Return dynamic inventory from source '''
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        try:
            self.mysql_port = 3306
            self.mysql_db = self.get_option('mysql_db')
            self.mysql_user = self.get_option('mysql_user')
            self.mysql_pass = self.get_option('mysql_pass')
            self.mysql_host = self.get_option('mysql_server')
            self.mysql_query = self.get_option('query_string')
        except Exception as e:
            raise AnsibleParserError(
                'All correct options required: {}'.format(e))
        self._populate()
