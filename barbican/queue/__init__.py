# Copyright (c) 2013-2014 Rackspace, Inc.
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
Queue objects for Cloudkeep's Barbican
"""
from oslo.config import cfg
from oslo import messaging

from barbican.common import exception
from barbican.common import utils
from barbican.openstack.common import gettextutils as u


LOG = utils.getLogger(__name__)

queue_opt_group = cfg.OptGroup(name='queue',
                               title='Queue Application Options')

queue_opts = [
    cfg.BoolOpt('enable', default=False,
                help=u._('True enables queuing, False invokes '
                         'workers synchronously')),
    cfg.StrOpt('namespace', default='barbican',
               help=u._('Queue namespace')),
    cfg.StrOpt('topic', default='barbican.workers',
               help=u._('Queue topic name')),
    cfg.StrOpt('version', default='1.1',
               help=u._('Version of tasks invoked via queue')),
    cfg.StrOpt('server_name', default='barbican.queue',
               help=u._('Server name for RPC task processing server')),
    cfg.IntOpt('task_max_retries', default=0,
               help=u._('Maximum times to retry a failed task')),
    cfg.IntOpt('task_retry_seconds', default=60,
               help=u._('Seconds to wait between retries for failed tasks')),
    cfg.FloatOpt('task_retry_tg_initial_delay', default=10.0,
                 help=u._('Seconds (float) to wait between '
                          'starting retry scheduler')),
    cfg.FloatOpt('task_retry_tg_periodic_interval_max', default=10.0,
                 help=u._('Seconds (float) to wait between '
                          'starting retry scheduler')),
    cfg.IntOpt('task_retry_scheduler_cycle', default=20,
               help=u._('Seconds for retry scheduler cycle')),
]

CONF = cfg.CONF
CONF.register_group(queue_opt_group)
CONF.register_opts(queue_opts, group=queue_opt_group)


TRANSPORT = None

ALLOWED_EXMODS = [
    exception.__name__,
]


def get_allowed_exmods():
    return ALLOWED_EXMODS


def init(conf):
    global TRANSPORT
    exmods = get_allowed_exmods()
    TRANSPORT = messaging.get_transport(conf,
                                        allowed_remote_exmods=exmods)


def cleanup():
    global TRANSPORT
    assert TRANSPORT is not None
    TRANSPORT.cleanup()
    TRANSPORT = None


def get_target():
    return messaging.Target(topic=CONF.queue.topic,
                            namespace=CONF.queue.namespace,
                            version=CONF.queue.version,
                            server=CONF.queue.server_name)


def get_client(target=None, version_cap=None, serializer=None):
    if not CONF.queue.enable:
        return None

    assert TRANSPORT is not None
    queue_target = target or get_target()
    return messaging.RPCClient(TRANSPORT,
                               target=queue_target,
                               version_cap=version_cap,
                               serializer=serializer)


def get_server(target, endpoints, serializer=None):
    assert TRANSPORT is not None
    return messaging.get_rpc_server(TRANSPORT,
                                    target,
                                    endpoints,
                                    executor='eventlet',
                                    serializer=serializer)
