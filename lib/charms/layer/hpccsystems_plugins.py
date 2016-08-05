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
from charmhelpers.core.hookenv import log
# log level: CRITICAL,ERROR,WARNING,INFO,DEBUG
from charmhelpers.core.hookenv import CRITICAL
from charmhelpers.core.hookenv import ERROR
from charmhelpers.core.hookenv import WARNING
from charmhelpers.core.hookenv import INFO
from charmhelpers.core.hookenv import DEBUG
#from charmhelpers.core import templating

import charms.layer.utils
from charms.layer.hpccenv import HPCCEnv


from charmhelpers.fetch.archiveurl import (
    ArchiveUrlFetchHandler
)

#import charm.apt
     

class HPCCSystemsPluginsConfigs:
    def __init__(self):
        self.config = hookenv.config()
        
    def install(self):
        self.install_prerequisites() 
        self.install_platform()

    def get_plugin_package_name(self, plugin_name):
        return "hpccsystems-platform-" + plugin_name + "_" +  \
               self.config['hpcc-version'] + platform.linux_distribution()[2] + "_amd64.deb"

    def get_plugin_package_url(self, plugin_name):
        hpcc_version_mmp = (self.config['hpcc-version']).split('-',1)[0]
        return self.config['base-url'] + "/" + self.config['hpcc-type'] + "-Candidate-" + \
               hpcc_version_mmp + "/bin/plugins/" + self.get_plugin_package_name(plugin_name)

    def download_plugins(self, plugin_name):
        hookenv.status_set('maintenance', 'Downloading plugin ' + plugin_name)
        url = self.get_plugin_package_url(plugin_name)
        package = self.get_plugin_package_name()
        log("Plugin package url: " + url, INFO)
        aufh =  ArchiveUrlFetchHandler()
        dest_file = "/tmp/" + package
        aufh.download(url, dest_file)
        fetch.apt_update()

        hash_key = plugin_name + '-hash' 
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

    def installed_platform(self, plugin_name):
        p = re.compile(r".*hpccsystems-plugin-${plugin_name}[\s]+([^\s]+)\s+([^\s]+)[\s]+hpccsystems-pluginl-${plugin_name}\\.*", re.M)
        try:
            output = check_output(['dpkg-query', '-l', 'hpccsystems-plugin-'+plugin_name])
            m = p.match(str(output))
            if m:
                return [m.group(1),m.group(2)]
            else:
                return ['','']
        except CalledProcessError:
             return ['','']

    def install_prerequsites(self):
        hookenv.status_set('maintenance', 'Installing prerequisites')
        charm_dir = hookenv.charm_dir()

        prereq_dir =  charm_dir + '/dependencies/' + platform.linux_distribution()[2] 
        with open(os.path.join(prereq_dir,'community.yaml')) as fp:
            workload = yaml.safe_load(fp)
        packages = workload['packages']
        addition_file = ""
        hpcc_type = self.config['hpcc-type']
        if hpcc_type == "EE":
            addition_file = os.path.join(prereq_dir, "enterprise.yaml")
        elif hpcc_type == "LN":
            addition_file = os.path.join(prereq_dir, "internal.yaml")
        if addition_file:
            with open(addition_file) as fp:
                workload = yaml.safe_load(fp)
            packages.extend(workload['packages'])
        fetch.apt_install(fetch.filter_installed_packages(packages))

    def open_ports(self):
        hookenv.status_set('maintenance', 'Open ports')
        #hookenv.open_port(self.config['esp-port'], 'TCP')
        hookenv.open_port(8010, 'TCP')
        hookenv.open_port(8002, 'TCP')
        hookenv.open_port(8015, 'TCP')
        hookenv.open_port(9876, 'TCP')
        #hookenv.open_port(self.config['esp-secure-port'], 'TCP')
        hookenv.open_port(18010, 'TCP')
        hookenv.open_port(18002, 'TCP')
        hookenv.open_port(18008, 'TCP')

    def start(self):
        hookenv.status_set('maintenance', 'Starting HPCC')
        log(HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init start', INFO)
        try: 
            output = check_output([HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init', 'start'])
            log(output, INFO)
        except CalledProcessError as e:
            log(e.output, ERROR)
            return 1

    def stop(self):
        hookenv.status_set('maintenance', 'Stopping HPCC')
        log(HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init stop', INFO)
        try: 
            output = check_output([HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init', 'stop'])
            log(output, INFO)
        except CalledProcessError as e:
            log(e.output, ERROR)
            return 1

    def restart(self):
        hookenv.status_set('maintenance', 'Restarting HPCC')
        log(HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init stop', INFO)
        try: 
            output = check_output([HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init', 'restart'])
            log(output, INFO)
        except CalledProcessError as e:
            log(e.output, ERROR)
            return 1

    def is_running(self):
        try: 
            output = check_output([HPCCEnv.HPCC_HOME+'/etc/init.d/hpcc-init', 'restart'])
            log(output, INFO)
            return true
        except CalledProcessError as e:
            log(e.output, INFO)
            return false

    def generate_env_xml(self, nodeTypes):
        self.process_nodes(nodeTypes)
        # future, create yaml file for envgen
        # self.create_envgen_yaml()
        #check_call(dpkg_install_platform_deb.split(), shell=False)
        cmd = self.create_envgen_cmd()
        log(cmd, INFO)
        try:
            output =  check_call(cmd.split(), shell=False)
            log(output, INFO)
        except CalledProcessError as e:
            log(e.output, ERROR)
            return 1
  
    def create_envgen_yaml(self):
        pass

    # when create_envgen_yaml available no need for this 
    def create_envgen_cmd(self):
        cmd = HPCCEnv.HPCC_HOME + '/sbin/envgen -env ' + \
              HPCCEnv.CONFIG_DIR + '/' +  HPCCEnv.ENV_XML_FILE + \
              ' -override roxie,@roxieMulticastEnabled,false' + \
              ' -override thor,@replicateOutputs,true' + \
              ' -override esp,@method,htpasswd' + \
              ' -override thor,@replicateAsync,true'  
        for key in nodes.key():
            nodeType=key.split('_')[0] 
            if nodeType == 'support':
                with open( HPCCEnv.CLUSTER_IPS_DIR + '/' + key, 'r') as file:
                    ip = re.sub('[\s+]', '', file.read())
                cmd = cmd + ' -ip ' + ip + ' -supportnodes 1'
                continue
            if nodeType == 'thor':
               cmd = cmd + ' -thornodes ' + str(nodes[k]) + \
                     ' -slavesPerNode ' + self.config['slaves-per-node']
            elif nodeType == 'roxie':
               cmd = cmd + ' -roxienodes ' + str(nodes[k])  
            cmd = cmd + ' -assign_ips ' + nodeType + ':file ' +  \
                  HPCCEnv.CLUSTER_IPS_DIR + '/' + key
        return cmd
              
