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

import copy
import uuid

from lxml import etree
from webob import exc

from nova.api.openstack import compute
from nova.api.openstack.compute.contrib import scheduled_images
from nova import db
from nova import exception
from nova.openstack.common import jsonutils
from nova.openstack.common import policy
from nova import test
from nova.tests.api.openstack import fakes


OS_SI = 'OS-SI:image_schedule'


class ScheduledImagesPolicyTest(test.TestCase):
    def setUp(self):
        super(ScheduledImagesPolicyTest, self).setUp()
        self.controller = scheduled_images.ScheduledImagesController()

    def test_get_image_schedule_restricted_by_project(self):
        rules = policy.Rules({'compute:get': policy.parse_rule(''),
                              'compute_extension:scheduled_images':
                               policy.parse_rule('project_id:%(project_id)s')})
        policy.set_rules(rules)

        def fake_instance_system_metadata_get(context, instance_id):
            return {'OS-SI:image_schedule': '7'}

        self.stubs.Set(db, 'instance_system_metadata_get',
                fake_instance_system_metadata_get)
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        self.assertRaises(exception.NotAuthorized, self.controller.index, req,
                          str(uuid.uuid4()))

    def test_post_image_schedule_restricted_by_project(self):
        rules = policy.Rules({'compute:get': policy.parse_rule(''),
                              'compute_extension:scheduled_images':
                               policy.parse_rule('project_id:%(project_id)s')})
        policy.set_rules(rules)

        def fake_instance_system_metadata_get(context, instance_id):
            return {'OS-SI:image_schedule': '6'}

        def fake_instance_system_metadata_update(context, instance_id,
                system_metadata, delete):
            return {'OS-SI:image_schedule': '7'}

        self.stubs.Set(db, 'instance_system_metadata_get',
                fake_instance_system_metadata_get)
        self.stubs.Set(db, 'instance_system_metadata_update',
                fake_instance_system_metadata_update)
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        req.method = 'POST'
        req.content_type = 'application/json'
        body = {"image_schedule": {"retention": "7"}}
        req.body = jsonutils.dumps(body)
        self.assertRaises(exception.NotAuthorized, self.controller.create, req,
                          str(uuid.uuid4()))

    def test_delete_image_schedule_restricted_by_project(self):
        rules = policy.Rules({'compute:get': policy.parse_rule(''),
                              'compute_extension:scheduled_images':
                               policy.parse_rule('project_id:%(project_id)s')})
        policy.set_rules(rules)

        def fake_instance_system_metadata_get(context, instance_id):
            return {'OS-SI:image_schedule': '7'}

        def fake_instance_system_metadata_update(context, instance_id,
                system_metadata, delete):
            return {}

        self.stubs.Set(db, 'instance_system_metadata_get',
                fake_instance_system_metadata_get)
        self.stubs.Set(db, 'instance_system_metadata_update',
                fake_instance_system_metadata_update)
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        self.assertRaises(exception.NotAuthorized, self.controller.delete, req,
                          str(uuid.uuid4()))


class ScheduledImagesTest(test.TestCase):
    def setUp(self):
        super(ScheduledImagesTest, self).setUp()
        self.controller = scheduled_images.ScheduledImagesController()

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

    def test_get_image_schedule(self):
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        res = self.controller.index(req, self.uuid_1)
        self.assertEqual(res, {"image-schedule": {"retention": "6"}})

    def test_post_image_schedule(self):
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        body = {"image_schedule": {"retention": "7"}}
        res = self.controller.create(req, self.uuid_1, body)
        self.assertEqual(res, {"image-schedule": {"retention": "7"}})

    def test_delete_image_schedule(self):
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
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
            inst['name'] = 'instance-1'  # this is a property
            inst['task_state'] = ''
            inst['vm_state'] = ''
            # NOTE(vish): db create translates security groups into model
            #             objects. Translate here so tests pass
            #inst['security_groups'] = [{'name': group}
            #                           for group in inst['security_groups']]

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
            if instance_id==self.uuid_1:
                return {'OS-SI:image_schedule': '6'}
            else:
                return {}

        self.stubs.Set(db, 'instance_system_metadata_get',
                fake_instance_system_metadata_get)

        meta = {"OS-SI:image_schedule": "7"}
        def fake_instance_system_metadata_update(context, instance_id, meta,
                                                 delete):
            if instance_id==self.uuid_1:
                return {'OS-SI:image_schedule': '7'}
            else:
                return {}

        self.stubs.Set(db, 'instance_system_metadata_update',
                fake_instance_system_metadata_update)

    def assertScheduledImages(self, dict_, value):
        self.assert_(OS_SI in dict_)
        self.assertEqual(dict_[OS_SI], value)

    def test_index_servers_with_true_query(self):
        query = 'OS-SI:image_schedule=True'
        url = '/v2/123/servers?%s' % query
        req = fakes.HTTPRequest.blank(query)
        resp_obj = {'servers': [{'id': self.uuid_1}, {'id': self.uuid_2}]}
        res = self.controller.index(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_1, 'OS-SI:image_schedule': '6'}]}
        self.assertEqual(res, expect)

    def test_index_servers_with_false_query(self):
        query = 'OS-SI:image_schedule=False'
        url = '/v2/123/servers?%s' % query
        req = fakes.HTTPRequest.blank(query)
        resp_obj = {'servers': [{'id': self.uuid_1}, {'id': self.uuid_2}]}
        res = self.controller.index(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_2}]}
        self.assertEqual(res, expect)

    def test_show_server(self):
        req = fakes.HTTPRequest.blank(
            '/fake/servers/%s' % self.uuid_1)
        res = req.get_response(self.app)
        server_dict = jsonutils.loads(res.body)['server']
        self.assertScheduledImages(server_dict, '6')

        #resp_obj = {'servers': [{'id': self.uuid_1}]}
        #res = self.controller.show(req, resp_obj, self.uuid_1)
        #expect = {'servers': [{'id': self.uuid_1, 'OS-SI:image_schedule': '6'}]}
        #self.assertEqual(res, expect)

    def test_detail_servers(self):
        req = fakes.HTTPRequest.blank('/v2/123/servers/detail')
        resp_obj = {'servers': [{'id': self.uuid_1, 'foo': 'bar'},
                                {'id': self.uuid_2, 'baz': 'qux'}]}
        res = self.controller.detail(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_1,
                               'OS-SI:image_schedule': '6',
                               'foo': 'bar',
                              },
                              {'id': self.uuid_2,
                               'baz': 'qux',
                              }]
                 }
        self.assertEqual(res, expect)

    def test_detail_servers_with_true_query(self):
        query = 'OS-SI:image_schedule=True'
        req = fakes.HTTPRequest.blank('/v2/123/servers/detail?%s' % query)
        resp_obj = {'servers': [{'id': self.uuid_1, 'foo': 'bar'},
                                {'id': self.uuid_2, 'baz': 'qux'}]}
        res = self.controller.detail(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_1,
                               'OS-SI:image_schedule': '6',
                               'foo': 'bar',
                              }]
                 }
        self.assertEqual(res, expect)

    def test_detail_servers_with_false_query(self):
        query = 'OS-SI:image_schedule=False'
        req = fakes.HTTPRequest.blank('/v2/123/servers/detail?%s' % query)
        resp_obj = {'servers': [{'id': self.uuid_1, 'foo': 'bar'},
                                {'id': self.uuid_2, 'baz': 'qux'}]}
        res = self.controller.detail(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_2,
                               'baz': 'qux',
                              }]
                 }
        self.assertEqual(res, expect)
