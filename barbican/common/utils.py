# Copyright (c) 2013 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Common utilities for Barbican.
"""

import time
from oslo.config import cfg
import barbican.openstack.common.log as logging


host_opts = [
    cfg.StrOpt('host_href', default='localhost'),
]

CONF = cfg.CONF
CONF.register_opts(host_opts)


# Current API version
API_VERSION = 'v1'


def hostname_for_refs(keystone_id=None, resource=None):
    """Return the HATEOS-style return URI reference for this service."""
    ref = ['http://{0}/{1}'.format(CONF.host_href, API_VERSION)]
    if not keystone_id:
        return ref[0]
    ref.append('/' + keystone_id)
    if resource:
        ref.append('/' + resource)
    return ''.join(ref)


# Return a logger instance.
#   Note: Centralize access to the logger to avoid the dreaded
#   'ArgsAlreadyParsedError: arguments already parsed: cannot
#   register CLI option'
#   error.
def getLogger(name):
    return logging.getLogger(name)


class TimeKeeper(object):

    def __init__(self, name, logger = None):
        self.logger = logger or getLogger(__name__)
        self.name = name
        self.time_start = time.time()
        self.time_last = self.time_start
        self.elapsed = []

    def mark(self, note=None):
        time_curr = time.time()
        self.elapsed.append((time_curr, time_curr - self.time_last, note))
        self.time_last = time_curr

    def dump(self):
        self.logger.debug("Timing output for '{0}'".format(self.name))
        for timec, timed, note in self.elapsed:
            self.logger.debug("    time current/elapsed/notes:"
                         "{0:.3f}/{1:.0f}/{2}".format(timec, timed*1000.,
                                                        note))
        time_current = time.time()
        total_elapsed = time_current - self.time_start
        self.logger.debug("    Final time/elapsed:"
                          "{0:.3f}/{1:.0f}".format(time_current,
                                                   total_elapsed*1000.))
