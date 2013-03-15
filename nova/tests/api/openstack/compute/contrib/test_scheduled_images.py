# Copyright 2013 Rackspace Hosting
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from nova.api.openstack import compute
from nova.api.openstack.compute.contrib import scheduled_images
from nova.compute import api as compute_api
from nova import db
from nova.openstack.common import jsonutils
from nova import test
from nova.tests.api.openstack import fakes
from qonos.qonosclient import client as qonos_client


OS_SI = 'OS-SI:image_schedule'


class ScheduledImagesTest(test.TestCase):
    def setUp(self):
        super(ScheduledImagesTest, self).setUp()
        self.controller = scheduled_images.ScheduledImagesController()
        self.uuid_1 = 'b04ac9cd-f78f-4376-8606-99f3bdb5d0ae'
        self.uuid_2 = '6b8b2aa4-ae7b-4cd0-a7f9-7fa6d5b0195a'
        FAKE_INSTANCES = [
            fakes.stub_instance(1,
                                uuid=self.uuid_1,
                                auto_disk_config=False),
            fakes.stub_instance(2,
                                uuid=self.uuid_2,
                                auto_disk_config=True)
        ]

        def fake_instance_get(context, id_):
            for instance in FAKE_INSTANCES:
                if id_ == instance['id']:
                    return instance

        self.stubs.Set(db, 'instance_get', fake_instance_get)

        def fake_instance_get_by_uuid(context, uuid):
            for instance in FAKE_INSTANCES:
                if uuid == instance['uuid']:
                    return instance

        self.stubs.Set(db, 'instance_get_by_uuid',
                       fake_instance_get_by_uuid)

        def fake_instance_get_all(context, *args, **kwargs):
            return FAKE_INSTANCES

        self.stubs.Set(db, 'instance_get_all', fake_instance_get_all)
        self.stubs.Set(db, 'instance_get_all_by_filters',
                       fake_instance_get_all)

        def fake_instance_system_metadata_get(context, instance_id):
            return {'OS-SI:image_schedule': '6'}

        self.stubs.Set(db, 'instance_system_metadata_get',
                fake_instance_system_metadata_get)

        meta = {"OS-SI:image_schedule": "7"}

        def fake_instance_system_metadata_update(context, instance_id, meta,
                                                 delete):
            return {'OS-SI:image_schedule': '7'}

        self.stubs.Set(db, 'instance_system_metadata_update',
                fake_instance_system_metadata_update)

        def fake_qonos_client_list_schedules(cls, **kwargs):
            schedules = [{'id': 1}, {'id': 2}]
            return schedules

        self.stubs.Set(qonos_client.Client, 'list_schedules',
                fake_qonos_client_list_schedules)

        def fake_qonos_client_create_schedule(cls, schedule):
            return {}

        self.stubs.Set(qonos_client.Client, 'create_schedule',
                fake_qonos_client_create_schedule)

        def fake_qonos_client_delete_schedule(cls, schedules):
            return

        self.stubs.Set(qonos_client.Client, 'delete_schedule',
                fake_qonos_client_delete_schedule)

        def fake_qonos_client_update_schedule(cls, schedules, sch_body):
            return

        self.stubs.Set(qonos_client.Client, 'update_schedule',
                fake_qonos_client_update_schedule)

        def fake_scheduled_images_create_schedule(cls, req):
            return

        cls = scheduled_images.ScheduledImagesController
        self.stubs.Set(cls, '_create_image_schedule',
                fake_scheduled_images_create_schedule)

    def test_get_image_schedule(self):
        url = '/fake/servers/%s/os-si-image-schedule' % self.uuid_1
        req = fakes.HTTPRequest.blank(url)
        res = self.controller.index(req, self.uuid_1)
        self.assertEqual(res, {"image_schedule": {"retention": "6"}})

    def test_post_image_schedule(self):
        url = '/fake/servers/%s/os-si-image-schedule' % self.uuid_1
        req = fakes.HTTPRequest.blank(url)
        body = {"image_schedule": {"retention": "7"}}
        res = self.controller.create(req, self.uuid_1, body)
        self.assertEqual(res, {"image_schedule": {"retention": "7"}})

    def test_delete_image_schedule(self):
        url = '/fake/servers/%s/os-si-image-schedule' % self.uuid_1
        req = fakes.HTTPRequest.blank(url)
        req.method = 'DELETE'
        res = self.controller.delete(req, self.uuid_1)
        self.assertEqual(res.status_int, 202)


class ScheduledImagesFilterTest(test.TestCase):
    def setUp(self):
        super(ScheduledImagesFilterTest, self).setUp()
        self.controller = scheduled_images.ScheduledImagesFilterController()
        self.uuid_1 = 'b04ac9cd-f78f-4376-8606-99f3bdb5d0ae'
        self.uuid_2 = '6b8b2aa4-ae7b-4cd0-a7f9-7fa6d5b0195a'
        FAKE_INSTANCES = [
            fakes.stub_instance(1,
                                uuid=self.uuid_1,
                                auto_disk_config=False),
            fakes.stub_instance(2,
                                uuid=self.uuid_2,
                                auto_disk_config=True)
        ]

        def fake_instance_get(context, id_):
            for instance in FAKE_INSTANCES:
                if id_ == instance['id']:
                    return instance

        self.stubs.Set(db, 'instance_get', fake_instance_get)

        def fake_instance_get_by_uuid(context, uuid):
            for instance in FAKE_INSTANCES:
                if uuid == instance['uuid']:
                    return instance

        self.stubs.Set(db, 'instance_get_by_uuid',
                       fake_instance_get_by_uuid)

        def fake_instance_get_all(context, *args, **kwargs):
            return FAKE_INSTANCES

        self.stubs.Set(db, 'instance_get_all', fake_instance_get_all)
        self.stubs.Set(db, 'instance_get_all_by_filters',
                       fake_instance_get_all)

        def fake_instance_create(context, inst_, session=None):
            class FakeModel(dict):
                def save(self, session=None):
                    pass

            inst = FakeModel(**inst_)
            inst['id'] = 1
            inst['uuid'] = self.uuid_2
            inst['created_at'] = datetime.datetime(2010, 10, 10, 12, 0, 0)
            inst['updated_at'] = datetime.datetime(2010, 10, 10, 12, 0, 0)
            inst['progress'] = 0
            inst['name'] = 'instance-1'
            inst['task_state'] = ''
            inst['vm_state'] = ''

            def fake_instance_get_for_create(context, id_, *args, **kwargs):
                return (inst, inst)

            self.stubs.Set(db, 'instance_update_and_get_original',
                          fake_instance_get_for_create)

            def fake_instance_get_all_for_create(context, *args, **kwargs):
                return [inst]
            self.stubs.Set(db, 'instance_get_all',
                           fake_instance_get_all_for_create)
            self.stubs.Set(db, 'instance_get_all_by_filters',
                           fake_instance_get_all_for_create)

        self.app = compute.APIRouter(init_only=('servers'))

        def fake_instance_system_metadata_get(context, instance_id):
            if instance_id == self.uuid_1:
                return {'OS-SI:image_schedule': '6'}
            else:
                return {}

        self.stubs.Set(db, 'instance_system_metadata_get',
                fake_instance_system_metadata_get)

        meta = {"OS-SI:image_schedule": "7"}

        def fake_instance_system_metadata_update(context, instance_id, meta,
                                                 delete):
            if instance_id == self.uuid_1:
                return {'OS-SI:image_schedule': '7'}
            else:
                return {}

        self.stubs.Set(db, 'instance_system_metadata_update',
                fake_instance_system_metadata_update)

        def fake_delete(cls, context, id_):
            return

        self.stubs.Set(compute_api.API, 'delete', fake_delete)

    def assertScheduledImages(self, dict_, value, is_present=True):
        if is_present:
            self.assert_(OS_SI in dict_)
            self.assertEqual(dict_[OS_SI], value)
        else:
            self.assert_(OS_SI not in dict_)

    def test_index_servers_with_true_query(self):
        query = 'OS-SI:image_schedule=True'
        req = fakes.HTTPRequest.blank('/fake/servers?%s' % query)
        res = req.get_response(self.app)
        servers = jsonutils.loads(res.body)['servers']
        for server in servers:
            self.assertScheduledImages(server, '6', is_present=True)

    def test_index_servers_with_false_query(self):
        query = 'OS-SI:image_schedule=False'
        req = fakes.HTTPRequest.blank('/fake/servers?%s' % query)
        res = req.get_response(self.app)
        servers = jsonutils.loads(res.body)['servers']
        for server in servers:
            self.assertScheduledImages(server, '6', is_present=False)

    def test_show_server(self):
        req = fakes.HTTPRequest.blank(
            '/fake/servers/%s' % self.uuid_1)
        res = req.get_response(self.app)
        server = jsonutils.loads(res.body)['server']
        self.assertScheduledImages(server, '6', is_present=True)

    def test_detail_servers(self):
        req = fakes.HTTPRequest.blank('/fake/servers/detail')
        res = req.get_response(self.app)
        servers = jsonutils.loads(res.body)['servers']
        for server in servers:
            if server['id'] == self.uuid_1:
                self.assertScheduledImages(server, '6', is_present=True)
            else:
                self.assertScheduledImages(server, '6', is_present=False)

    def test_detail_servers_with_true_query(self):
        query = 'OS-SI:image_schedule=True'
        req = fakes.HTTPRequest.blank('/fake/servers/detail?%s' % query)
        res = req.get_response(self.app)
        servers = jsonutils.loads(res.body)['servers']
        for server in servers:
            self.assertScheduledImages(server, '6', is_present=True)

    def test_detail_servers_with_false_query(self):
        query = 'OS-SI:image_schedule=False'
        req = fakes.HTTPRequest.blank('/fake/servers/detail?%s' % query)
        res = req.get_response(self.app)
        servers = jsonutils.loads(res.body)['servers']
        for server in servers:
            self.assertScheduledImages(server, '6', is_present=False)

    def test_delete_server(self):
        query = 'OS-SI:image_schedule=False'
        req = fakes.HTTPRequest.blank('/fake/servers/%s' % self.uuid_2)
        req.method = 'DELETE'
        res = req.get_response(self.app)
        self.assertEqual(res.status_int, 204)
