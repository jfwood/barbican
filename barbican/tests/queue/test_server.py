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
import mock
from mock import patch

from barbican import queue
from barbican.queue import server
from barbican.tests import utils


class WhenUsingInvokerDecorator(utils.BaseTestCase):
    """Test using task invoker decorator."""

    def setUp(self):
        super(WhenUsingInvokerDecorator, self).setUp()

        self.args = ['foo', 'bar']
        self.kwargs = {'a': 1, 'b': 2}
        self.max_retries = 1
        self.retry_seconds = 20

        self.mock_task = mock.MagicMock()

        class TestTaskClass(object):
            def __init__(self, mock_task):
                super(TestTaskClass, self).__init__()
                self.mock_task = mock_task

            def mock_function(self, inst, context, fooval, *args, **kwargs):
                self.fooval = fooval
                self.args = args
                self.kwargs = kwargs
                return self.mock_task
        self.test_task_inst = TestTaskClass(self.mock_task)

        self.decorator_outer = server\
            .invocable_task(max_retries=self.max_retries,
                            retry_seconds=self.retry_seconds)
        self.decorator_inner = self\
            .decorator_outer(self.test_task_inst.mock_function)

    @patch('barbican.queue.server.get_retry_manager')
    def test_should_use_invocable_task(self, mock_get_retry_manager):
        mock_get_retry_manager.return_value = mock.MagicMock()
        mock_get_retry_manager.return_value.remove = mock.MagicMock()

        self.decorator_inner(self.test_task_inst, None, *self.args,
                             **self.kwargs)

        self.mock_task.get_name.assert_called_once_with()
        self.mock_task.process.assert_called_once_with(self.max_retries,
                                                       *self.args,
                                                       **self.kwargs)

        mock_get_retry_manager.return_value.remove\
            .assert_called_once_with('mock_function',
                                     *self.args,
                                     **self.kwargs)

        self.assertEqual('foo', self.test_task_inst.fooval)
        self.args.remove('foo')  # Remove arg that is position in test class.
        self.assertEqual(self.args, list(self.test_task_inst.args))
        self.assertEqual(self.kwargs, self.test_task_inst.kwargs)

    @patch('barbican.queue.server.get_retry_manager')
    def test_should_fail_invocable_task(self, mock_get_retry_manager):
        mock_get_retry_manager.return_value = mock.MagicMock()
        mock_get_retry_manager.return_value.retry = mock.MagicMock()

        # Force error when the task's process() is invoked.
        self.mock_task.process = mock.MagicMock(side_effect=ValueError())

        self.decorator_inner(self.test_task_inst, None, *self.args,
                             **self.kwargs)

        self.mock_task.get_name.assert_called_with()
        self.mock_task.process.assert_called_once_with(self.max_retries,
                                                       *self.args,
                                                       **self.kwargs)

        mock_get_retry_manager.return_value.retry\
            .assert_called_once_with('mock_function',
                                     self.max_retries,
                                     self.retry_seconds,
                                     *self.args,
                                     **self.kwargs)

        self.assertEqual('foo', self.test_task_inst.fooval)
        self.args.remove('foo')  # Remove arg that is position in test class.
        self.assertEqual(self.args, list(self.test_task_inst.args))
        self.assertEqual(self.kwargs, self.test_task_inst.kwargs)


class WhenUsingBeginOrderTask(utils.BaseTestCase):
    """Test using the Tasks class for 'order' task."""

    def setUp(self):
        super(WhenUsingBeginOrderTask, self).setUp()

        self.tasks = server.Tasks()
        self.max_retries = 0  # Zero retries expected, per default annotation

    @patch('barbican.tasks.resources.BeginOrder')
    def test_should_process_order(self, mock_begin_order):
        mock_begin_order.return_value.process.return_value = None
        self.tasks.process_order(context=None,
                                 order_id=self.order_id,
                                 keystone_id=self.keystone_id)
        mock_begin_order.return_value.process\
            .assert_called_with(self.max_retries, order_id=self.order_id,
                                keystone_id=self.keystone_id)


class WhenUsingPerformVerificationTask(utils.BaseTestCase):
    """Test using the Tasks class for 'verification' task."""

    def setUp(self):
        super(WhenUsingPerformVerificationTask, self).setUp()

        self.tasks = server.Tasks()
        self.max_retries = 0  # Zero retries expected, per default annotation

    @patch('barbican.tasks.resources.PerformVerification')
    def test_should_process_verification(self, mock_begin_verification):
        mock_begin_verification.return_value.process.return_value = None
        self.tasks.process_verification(context=None,
                                        verification_id=self.verification_id,
                                        keystone_id=self.keystone_id)
        mock_begin_verification.return_value.process\
            .assert_called_with(self.max_retries,
                                verification_id=self.verification_id,
                                keystone_id=self.keystone_id)


class WhenUsingTaskServer(utils.BaseTestCase):
    """Test using the asynchronous task client."""

    def setUp(self):
        super(WhenUsingTaskServer, self).setUp()

        self.target = 'a target value here'
        queue.get_target = mock.MagicMock(return_value=self.target)

        self.server_mock = mock.MagicMock()
        self.server_mock.start.return_value = None
        self.server_mock.stop.return_value = None

        queue.get_server = mock.MagicMock(return_value=self.server_mock)

        self.server = server.TaskServer()

    def test_should_start(self):
        self.server.start()
        queue.get_target.assert_called_with()
        queue.get_server.assert_called_with(target=self.target,
                                            endpoints=[self.server])
        self.server_mock.start.assert_called_with()

    def test_should_stop(self):
        self.server.stop()
        queue.get_target.assert_called_with()
        queue.get_server.assert_called_with(target=self.target,
                                            endpoints=[self.server])
        self.server_mock.stop.assert_called_with()


class WhenUsingTaskRetryManager(utils.BaseTestCase):
    """Test using the TaskRetryManager instance."""

    def setUp(self):
        super(WhenUsingTaskRetryManager, self).setUp()

        self.retry_method = 'do_something'
        self.args = ['foo', 'bar']
        self.kwargs = {'a': 1, 'b': 2}

        self.manager = server.TaskRetryManager()

    def test_should_generate_key(self):
        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)
        retry, arg_set, kwarg_set = key
        self.assertEqual(self.retry_method, retry)
        self.assertEqual(frozenset(self.args), arg_set)
        self.assertEqual(frozenset(self.kwargs.items()), kwarg_set)

    def test_should_retry(self):
        max_retries = 1
        retry_seconds = 20
        self.manager.retry(self.retry_method,
                           max_retries, retry_seconds,
                           *self.args, **self.kwargs)
        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)
        self.assertIn(key, self.manager.num_retries_so_far)
        self.assertEqual(1, self.manager.num_retries_so_far[key])

        self.assertIn(key, self.manager.countdown_seconds)
        self.assertEqual(retry_seconds, self.manager.countdown_seconds[key])

    def test_should_not_retry(self):
        max_retries = 0
        retry_seconds = 20
        self.manager.retry(self.retry_method,
                           max_retries, retry_seconds,
                           *self.args, **self.kwargs)
        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)
        self.assertNotIn(key, self.manager.num_retries_so_far)
        self.assertNotIn(key, self.manager.countdown_seconds)

    def test_should_remove_key(self):
        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)
        self.manager.num_retries_so_far[key] = 0
        self.manager.countdown_seconds[key] = 0
        self.manager.remove(self.retry_method, *self.args,
                            **self.kwargs)
        self.assertNotIn(key, self.manager.num_retries_so_far)
        self.assertNotIn(key, self.manager.countdown_seconds)

    def test_should_remove_key_instance(self):
        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)
        self.manager.num_retries_so_far[key] = 0
        self.manager.countdown_seconds[key] = 0
        self.manager._remove_key(key)
        self.assertNotIn(key, self.manager.num_retries_so_far)
        self.assertNotIn(key, self.manager.countdown_seconds)

        # Repeated deletes shouldn't raise exceptions.
        self.manager._remove_key(key)

    def test_should_invoke_client(self):
        class TestQueueClass(object):
            def do_something(self, fooval, *args, **kwargs):
                self.fooval = fooval
                self.args = args
                self.kwargs = kwargs
        queue = TestQueueClass()

        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)

        self.manager.num_retries_so_far[key] = 1
        self.manager.countdown_seconds[key] = 20
        self.manager._invoke_client_method(key, queue)

        self.assertIn('retries_so_far', queue.kwargs)
        self.assertEqual(1, queue.kwargs['retries_so_far'])
        self.kwargs['retries_so_far'] = 1  # Make = to key added by manager.
        self.assertEqual('foo', queue.fooval)

        self.args.remove('foo')  # Remove arg that is position in test class.
        self.assertEqual(self.args, list(queue.args))
        self.assertEqual(self.kwargs, queue.kwargs)

    def test_should_schedule(self):
        self.manager._invoke_client_method = mock.\
            MagicMock(side_effect=ValueError())
        self.manager._remove_key = mock.MagicMock()
        queue = mock.MagicMock()
        countdown_seconds = 9
        seconds_between_retries = 5

        key = self.manager._generate_key_for(self.retry_method,
                                             *self.args,
                                             **self.kwargs)

        self.manager.num_retries_so_far[key] = 1
        self.manager.countdown_seconds[key] = countdown_seconds

        # Check to see if task is ready to schedule (shouldn't be):
        seconds_between_retries_return = self.manager\
            .schedule_retries(seconds_between_retries, queue)

        self.assertEqual(seconds_between_retries,
                         seconds_between_retries_return)
        self.assertIn(key, self.manager.num_retries_so_far)
        self.assertIn(key, self.manager.countdown_seconds)
        self.assertEqual(countdown_seconds - seconds_between_retries,
                         self.manager.countdown_seconds[key])

        # Check to see if task is ready to schedule (shouldn't be):
        self.manager._invoke_client_method = mock.MagicMock()

        seconds_between_retries_return = self.manager\
            .schedule_retries(seconds_between_retries, queue)

        self.assertEqual(seconds_between_retries,
                         seconds_between_retries_return)
        self.manager._invoke_client_method.assert_called_once_with(key,
                                                                   queue)
        self.manager._remove_key.assert_called_once_with(key)
