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

from nova.api.openstack.compute.contrib import scheduled_images
from nova import db
from nova import exception
from nova.openstack.common import jsonutils
from nova.openstack.common import policy
from nova import test
from nova.tests.api.openstack import fakes


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
        res = self.controller.index(req, FAKE_UUID)
        self.assertEqual(res, {"image-schedule": {"retention": "6"}})

    def test_post_image_schedule(self):
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        body = {"image_schedule": {"retention": "7"}}
        res = self.controller.create(req, FAKE_UUID, body)
        self.assertEqual(res, {"image-schedule": {"retention": "7"}})

    def test_delete_image_schedule(self):
        req = fakes.HTTPRequest.blank('/v2/123/servers/12/os-si-image-schedule')
        res = self.controller.delete(req, FAKE_UUID)
        self.assertEqual(res.status_int, 202)


class ScheduledImagesFilterTest(test.TestCase):
    def setUp(self):
        super(ScheduledImagesTest, self).setUp()
        self.controller = scheduled_images.ScheduledImagesFilterController()
        self.uuid_1 = 'b04ac9cd-f78f-4376-8606-99f3bdb5d0ae'
        self.uuid_2 = '6b8b2aa4-ae7b-4cd0-a7f9-7fa6d5b0195a'

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

    def test_index_servers_with_true_query(self):
        query = 'OS-SI:image_schedule=True'
        url = '/v2/123/servers?%s' % query
        req = fakes.HTTPRequest.blank(query)
        resp_obj = {'servers': [{'id': self.uuid_1}, {'id': self.uuid_2}]}
        res = self.controller.index(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_1, 'OS-SI:image_schedule': '6'}]
        self.assertEqual(res, expect)

    def test_index_servers_with_false_query(self):
        query = 'OS-SI:image_schedule=False'
        url = '/v2/123/servers?%s' % query
        req = fakes.HTTPRequest.blank(query)
        resp_obj = {'servers': [{'id': self.uuid_1}, {'id': self.uuid_2}]}
        res = self.controller.index(req, resp_obj)
        expect = {'servers': [{'id': self.uuid_2}]
        self.assertEqual(res, expect)

    def test_show_server(self):
        server_id = FAKE_UUID
        url = '/v2/123/servers/%s' % server_id
        req = fakes.HTTPRequest.blank(query)
        resp_obj = {'servers': [{'id': self.uuid_1}]}
        res = self.controller.show(req, resp_obj, self.uuid_1)
        expect = {'servers': [{'id': self.uuid_1, 'OS-SI:image_schedule': '6'}]
        self.assertEqual(res, expect)

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
