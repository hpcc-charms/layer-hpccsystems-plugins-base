#!/usr/bin/env python3

import os
import platform
import yaml
import re
# python 2.7
#import ConfigParser
# python 3
#import Configparser
from subprocess import check_call,check_output,CalledProcessError
 
from charmhelpers import fetch
from charmhelpers.core import host
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import (
    log,
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG
)
#from charmhelpers.core import templating

from charms.layer.utils import package_extension
from charms.layer.hpccenv import HPCCEnv


from charmhelpers.fetch.archiveurl import (
    ArchiveUrlFetchHandler
)

#import charm.apt
     

class HPCCSystemsPluginConfig:
    def __init__(self):
        self.config = hookenv.config()
        
    def install(self):

        #naviagate plugins
        for plugin in self.config['plugins'].split(','):
          self.install_prerequisites(plugin) 
          self.install_plugin(plugin)

    def get_plugin_package_name(self, plugin_name):
        #log('package-prefix: ' + self.config['package-prefix'], "INFO") 
        #log('plugin_name: ' + plugin_name, "INFO") 
        #log('name-version-seperator: ' + self.config['name-version-seperator'], "INFO") 
        #log('version: ' + self.config['version'], "INFO") 
        #log('extension: ' + package_extension(), "INFO") 
        return self.config['package-prefix'] + plugin_name + \
               self.config['name-version-seperator'] + \
               self.config['version'] + package_extension()

    def get_plugin_package_url(self, plugin_name):
        version_mmp = (self.config['version']).split('-',1)[0]
        if self.config['package-prefix'] == 'hpccsystems-plugin-':
             package_dir = 'plugins'
        else:
             package_dir = plugin_name
        return self.config['base-url'] + "/" + "CE-Candidate-" + \
               version_mmp + "/bin/" + package_dir + "/" + \
               self.get_plugin_package_name(plugin_name)

    def download_plugin(self, plugin_name):
        hookenv.status_set('maintenance', 'Downloading plugin ' + plugin_name)
        url = self.get_plugin_package_url(plugin_name)
        package = self.get_plugin_package_name(plugin_name)
        log("Plugin package url: " + url, INFO)
        aufh =  ArchiveUrlFetchHandler()
        dest_file = "/tmp/" + package
        aufh.download(url, dest_file)
        fetch.apt_update()

        hash_key = plugin_name + '-hash' 
        checksum = ''
        if hash_key in self.config.keys(): 
           checksum = self.config[hash_key]
        if checksum:
            hash_type = self.config['hash-type']
            if not hash_type:
                hash_type = 'md5'
            host.check_hash(dest_file, checksum, hash_type)
        return dest_file

    def install_plugin(self, plugin_name):
        hookenv.status_set('maintenance', 'Installing plugin ' + plugin_name)
        package_file = self.download_plugin(plugin_name)
        dpkg_install_plugin_deb = 'dpkg -i %s' % package_file
        check_call(dpkg_install_plugin_deb.split(), shell=False)

    def uninstall_plugin(self, plugin_name):
        hookenv.status_set('maintenance', 'Uninstalling plugin ' + plugin_name)
        dpkg_uninstall_plugin_deb = 'dpkg --purage hpccsystems-plugin-' + plugin_name
        check_call(dpkg_uninstall_plugin_deb.split(), shell=False)

    def installed_plugin(self, plugin_name):
        
        prefix    =  self.config['package-prefix'] 
        p = re.compile(r".*${prefix}${plugin_name}[\s]+([^\s]+)\s+([^\s]+)[\s]+${prefix}${plugin_name}\\.*", re.M)
        try:
            output = check_output(['dpkg-query', '-l', prefix+plugin_name])
            m = p.match(str(output))
            if m:
                return [m.group(1),m.group(2)]
            else:
                return ['','']
        except CalledProcessError:
             return ['','']

    def install_prerequisites(self, plugin_name):
        hookenv.status_set('maintenance', 'Installing prerequisites')
        charm_dir = hookenv.charm_dir()

        prereq_dir =  charm_dir + '/dependencies/' + platform.linux_distribution()[2] 
        with open(os.path.join(prereq_dir, plugin_name + '.yaml')) as fp:
            workload = yaml.safe_load(fp)
        packages = workload['packages']
        fetch.apt_install(fetch.filter_installed_packages(packages))
