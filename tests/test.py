# ------------------------------------------------------------------------------
# Copyright 2021 Mohammad Reza Golsorkhi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
# name: test.py
# Description: test the functionality of agent and job and other part of package
# Version: 0.1.3
# Author: Mohammad Reza Golsorkhi
# ------------------------------------------------------------------------------


import datetime
import time
from unittest import TestCase

from src.agent import Agent, job


def _test_func(t):
    print('I am running')
    c = t[0]
    t.append('in test func {}'.format(str(c)))
    t[0] += 1
    print(t)


def _test_func_list_int_str(t):
    c = t[0] + 1
    t[0] = c
    t[1] = str(c)
    time.sleep(2)


class TestAgent(TestCase):
    options = {
        'scheduler': 'interval',
        'start_time': datetime.datetime.now(),
        'interval': 1
    }

    def test_run_job_by_id_and_name(self):
        agent = Agent()
        t = [0, '0']
        agent.create_job(func=_test_func_list_int_str,
                         options=TestAgent.options, args=(t,), name='norm2')

        @agent.create_job_decorator(options=TestAgent.options, args=(t,), name='dec2')
        def test_func_list_int_str_inner_and_job_is_running(t):
            c = t[0] + 1
            t[0] = c
            t[1] = str(c)
            time.sleep(2)

        agent.run_job_by_name('norm2')
        time.sleep(2.1)
        self.assertEqual([1, '1'], t)

        agent.run_job_by_id(agent.get_job_by_name('dec2').id)
        time.sleep(2)
        self.assertEqual([2, '2'], t)
        self.assertEqual(0, agent.run_job_by_id(Agent._job_id_counter + 1))
        self.assertEqual(0, agent.run_job_by_name('asx'))
        self.assertEqual(2, len(agent.get_all_jobs()))
        self.assertIsNone(agent.get_job_by_id(Agent._job_id_counter + 1))
        del agent

    def test_agent(self):
        agent = Agent()
        t = [1]
        print('job_id IS ' + str(id(t)))
        agent.create_job(func=_test_func, options=TestAgent.options, args=(t,), name='job_1')
        agent.start()
        print(t)
        time.sleep(1)
        self.assertIn('in test func 1', t)
        agent.stop()

    def test_Job(self):
        options = {
            'scheduler': 'interval',
            'start_time': datetime.datetime.now(),
            'interval': 1
        }

        agent = Agent()
        t = [1]
        print('job_id IS ' + str(id(t)))

        class J(job.Job):
            def run(self, *args, **kwargs):
                print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

        agent.create_class_job(job=J, options=options)
        agent.start()
        #print(t)
        time.sleep(10)
        #self.assertIn('in test func 1', t)
        agent.stop()

    def test_agent_stop(self):
        agent = Agent()
        t = [0, '0']
        agent.create_job(func=_test_func_list_int_str,
                         options=TestAgent.options, args=(t,), name='job_2')
        agent.start()
        time.sleep(0.1)
        self.assertEqual([1, '1'], t)
        print(t)
        time.sleep(3)
        print(t)
        self.assertEqual([2, '2'], t)
        print(t)
        agent.stop()
        print(t)
        time.sleep(3)
        self.assertEqual([2, '2'], t)

    @staticmethod
    def custom_interval(interval, job):

        if job.next_run_time is None:
            try:
                r = job.options['start_time']
            except KeyError:
                raise KeyError('start_time not fond')
        else:
            r = job.next_run_time + datetime.timedelta(seconds=interval)
        print('this is custom interval returning {}'.format(str(r)))
        return r

    def test_custom_CNRT(self):
        _options = {
            'scheduler': 'custom',
            'start_time': datetime.datetime.now(),
            'custom_time_scheduler': self.custom_interval,
            'scheduler_args': (1,)
        }
        agent = Agent()
        t = [0, '0']
        agent.create_job(func=_test_func_list_int_str,
                         options=_options, args=(t,), name='job_3')
        agent.start()
        time.sleep(0.5)
        self.assertEqual([1, '1'], t)
        print(t)
        time.sleep(3)
        print(t)
        self.assertEqual([2, '2'], t)
        print(t)
        agent.stop()
        print(t)
        time.sleep(3)
        self.assertEqual([2, '2'], t)

    def test_job_return(self):
        agent = Agent()

        @agent.create_job_decorator(options=TestAgent.options, name='job_4')
        def test_func_list_int_str_inner_and_job_is_running():
            time.sleep(1)
            return 5

        agent.start()
        job = agent.get_job_by_name('job_4')
        self.assertIsNone(job.status.get('last_return'))
        time.sleep(2)
        print(job.status.get('last_return'))
        self.assertEqual(job.status.get('last_return'), 5)
        agent.stop()

    def test_job_fail_handler(self):
        def jfh(exception, job):
            job.status['jfh'] = 'Test'
            job.status['exception'] = exception

        options = {
            'scheduler': 'interval',
            'start_time': datetime.datetime.now(),
            'interval': 1,
            'job_fail_handler': {
                'Handler': 'custom',
                'custom_job_fail_Handler': jfh
            }
        }
        agent = Agent()

        @agent.create_job_decorator(options=options, name='job_5')
        def test_func_list_int_str_inner_and_job_is_running():
            time.sleep(1)
            raise Exception('test_exception')

        agent.start()
        job = agent.get_job_by_name('job_5')
        self.assertIsNone(job.status.get('jfh'))
        time.sleep(2)
        print(job.status.get('last_return'))
        self.assertEqual(job.status.get('jfh'), 'Test')
        agent.stop()

    def test_job_restart_after_fail_force_restart_job(self):
        from src.agent.handler import JobFailHandler

        options = {
            'scheduler': 'interval',
            'start_time': datetime.datetime.now(),
            'interval': 100,
            'job_fail_handler': {
                'Handler': 'restart_after_fail',
                'num_restart_trys_after_fail': 2,
                'overwrite_agent_not_running': JobFailHandler.OverwriteAgentNotRunning.force_restart_job
            }
        }
        agent = Agent()

        @agent.create_job_decorator(options=options, name='job_6')
        def test_func_list_int_str_inner_and_job_is_running(job):
            time.sleep(0.5)
            if job.status.get('jfh'):
                job.status['jfh'] = int(job.status['jfh']) + 1

            else:
                job.status['jfh'] = 1
            raise Exception('test_exception')

        job = agent.get_job_by_name('job_6')
        agent.run_job_by_name('job_6')

        print(job.status)
        self.assertIsNone(job.status.get('jfh'))

        time.sleep(0.6)
        print(job.status)
        self.assertEqual(job.status['jfh'], 1)

        print(job.status)
        time.sleep(0.6)
        self.assertEqual(job.status['jfh'], 2)

        print(job.status)
        time.sleep(0.7)
        self.assertEqual(job.status['jfh'], 3)
        print(job.status)
        time.sleep(0.7)
        self.assertEqual(job.status['jfh'], 3)

    def test_job_restart_after_fail_force_run_agent(self):
        from src.agent.handler import JobFailHandler

        options = {
            'scheduler': 'interval',
            'start_time': datetime.datetime.now(),
            'interval': 100,
            'job_fail_handler': {
                'Handler': 'restart_after_fail',
                'num_restart_trys_after_fail': 2,
                'overwrite_agent_not_running': JobFailHandler.OverwriteAgentNotRunning.force_run_agent
            }
        }
        agent = Agent()

        @agent.create_job_decorator(options=options, name='job_7')
        def test_func_list_int_str_inner_and_job_is_running(job):
            time.sleep(0.5)
            if job.status.get('jfh'):
                job.status['jfh'] = int(job.status['jfh']) + 1

            else:
                job.status['jfh'] = 1
            raise Exception('test_exception')

        job = agent.get_job_by_name('job_7')
        agent.run_job_by_name('job_7')

        print(job.status)
        self.assertIsNone(job.status.get('jfh'))

        time.sleep(0.6)
        print(job.status)
        self.assertEqual(job.status['jfh'], 1)

        print(job.status)
        time.sleep(0.6)
        self.assertEqual(job.status['jfh'], 2)

        print(job.status)
        time.sleep(0.9)
        self.assertEqual(job.status['jfh'], 3)
        print(job.status)
        time.sleep(0.7)
        self.assertEqual(job.status['jfh'], 3)
        agent.stop()

    def test_job_stop(self):

        agent = Agent()

        @agent.create_job_decorator(options=self.options, name='job_8')
        def test_func_list_int_str_inner_and_job_is_running():
            time.sleep(10)
            return 10

        job = agent.get_job_by_name('job_8')
        time.sleep(0.5)
        job.start()
        time.sleep(0.5)
        job.stop(1)
        time.sleep(2.5)
        print(job.status)
        self.assertIsNone(job.status.get('last_return'))

    def test_save_and_load(self):
        agent = Agent()
        agent.create_job(func=_test_func, name='job_a1', options=self.options)
        agent.save_job(job=agent.get_job_by_name('job_a1'), dirpath=r'tests')
        agent.load_job(filepath=r'tests/job_a1.job')
        job_a1 = agent.get_job_by_name('job_a1')
        job_a1_loaded = agent.get_job_by_name('job_a1 (1)')
        self.assertEqual(job_a1_loaded._func.__code__.co_code, job_a1._func.__code__.co_code)

    def test_dumps_and_loads(self):
        agent = Agent()
        agent.create_job(func=_test_func, name='job_a1', options=self.options)
        s = agent.dumps_job(job=agent.get_job_by_name('job_a1'))
        agent.loads_job(str=s)
        job_a1 = agent.get_job_by_name('job_a1')
        job_a1_loaded = agent.get_job_by_name('job_a1 (1)')
        self.assertEqual(job_a1_loaded._func.__code__.co_code, job_a1._func.__code__.co_code)
