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
Simple Queue Resources related objects and functions, making direct calls
to the worker tasks.
"""
from oslo.config import cfg
from barbican.tasks.resources import BeginOrder
from barbican.common import utils

LOG = utils.getLogger(__name__)

CONF = cfg.CONF


def process_order(order_id, keystone_id):
    """Process Order."""
    LOG.debug('Order id is {0}'.format(order_id))
    task = BeginOrder()
    return task.process(order_id, keystone_id)
