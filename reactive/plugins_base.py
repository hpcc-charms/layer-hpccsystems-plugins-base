#!/usr/bin/env python3
#import os
#import platform
#import yaml
#from subprocess import check_call

from charms.reactive.helpers import is_state
from charms.reactive.bus import set_state
from charms.reactive.bus import get_state
from charms.reactive.bus import remove_state
from charms.reactive.decorators import hook
from charms.reactive.decorators import when
from charms.reactive.decorators import when_not

from charmhelpers.core import hookenv 
from charmhelpers.core.hookenv import  (
    log,
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    status_set
)


from charms.layer.hpccsystems_plugin import HPCCSystemsPluginConfig

@hook('install')
def install_plugin():
    plugin = HPCCSystemsPluginConfig()
    plugin.install()
    status_set('maintenance', 'installing plugin')


#@hook('config-changed')
#def config_changed():
#    config = hookenv.config()
#    if config.changed('ssh-key-private'): 
#        install_keys_from_config(config)
#
#    platform = HPCCSystemsPlatformConfig()
#    if config.changed('hpcc-version') or config.changed('hpcc-type'): 
#       hpcc_installed = platform.installed_platform()
#       if (config.changed('hpcc-version') != hpcc_installed[0]) or \
#          (config.changed('hpcc-type') != hpcc_installed[1]) : 
#          remove_state('platform.installed')
#          platform.uninstall_platform()
#          platform.install_platform()
#          set_state('platform.installed')
 

