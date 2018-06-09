"""Test for checking if the response format is proper. Run test_crud before running this."""
# -*- coding: utf-8 -*-

import unittest
import random
import string
import json
import re
from hydrus.app import app_factory
from hydrus.utils import Getter_setter
from hydrus.data import doc_parse
from hydrus.hydraspec import doc_writer_sample, doc_maker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from hydrus.data.db_models import Base
from falcon import testing


def gen_dummy_object(class_, doc):
    """Create a dummy object based on the definitions in the API Doc."""
    object_ = {
        "@type": class_
    }
    if class_ in doc.parsed_classes:
        for prop in doc.parsed_classes[class_]["class"].supportedProperty:
            if "vocab:" in prop.prop:
                prop_class = prop.prop.replace("vocab:", "")
                object_[prop.title] = gen_dummy_object(prop_class, doc)
            else:
                object_[prop.title] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return object_


class ViewsTestCase(testing.TestCase):
    """Test Class for the app."""

    def setUp(self):
        """Database setup before the tests."""
        super(ViewsTestCase, self).setUp()
        print("Creating a temporary database...")
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        self.session = scoped_session(sessionmaker(bind=engine))
        self.HYDRUS_SERVER_URL =  "http://hydrus.com"
        self.API_NAME = "demoapi"
        self.doc = doc_maker.create_doc(doc_writer_sample.api_doc.generate(), self.HYDRUS_SERVER_URL, self.API_NAME)
        self.gs = Getter_setter(self.session, self.HYDRUS_SERVER_URL, self.API_NAME, self.doc, False)
        self.app = app_factory(self.API_NAME, self.gs)
        test_classes = doc_parse.get_classes(self.doc.generate())
        test_properties = doc_parse.get_all_properties(test_classes)
        doc_parse.insert_classes(test_classes, self.session)
        doc_parse.insert_properties(test_properties, self.session)

        print("Classes and properties added successfully.")

        print("Setting up Hydrus utilities... ")
        print("Creating utilities context... ")
        print("Setup done, running tests...")

class TestCases(ViewsTestCase):

    def test_Index(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        print(response_get.json)
        endpoints = response_get.json
        response_post = self.simulate_post("/"+self.API_NAME, json=dict(foo="bar"))
        response_put = self.simulate_put("/"+self.API_NAME, json=dict(foo="bar"))
        response_delete = self.simulate_delete("/"+self.API_NAME)
        assert "@context" in endpoints
        assert endpoints["@id"] == "/"+self.API_NAME
        assert endpoints["@type"] == "EntryPoint"
        assert response_get.status_code == 200
        assert response_post.status_code == 405
        assert response_put.status_code == 405
        assert response_delete.status_code == 405

    def test_EntryPoint_context(self):
        """Test for the EntryPoint context."""
        response_get = self.simulate_get("/"+self.API_NAME + "/contexts/EntryPoint.jsonld")
        response_get_data = response_get.json
        response_post = self.simulate_post("/"+self.API_NAME + "/contexts/EntryPoint.jsonld", json={})
        response_delete = self.simulate_delete("/"+self.API_NAME + "/contexts/EntryPoint.jsonld")
        assert response_get.status_code == 200
        assert "@context" in response_get_data
        assert response_post.status_code == 405
        assert response_delete.status_code == 405

    def test_Vocab(self):
        """Test the vocab."""
        response_get = self.simulate_get("/"+ self.API_NAME + "/vocab")
        print(response_get.text)
        response_get_data = response_get.json

        assert "@context" in response_get_data
        assert response_get_data["@type"] == "ApiDocumentation"
        assert response_get_data["@id"] == self.HYDRUS_SERVER_URL + self.API_NAME + "/vocab"
        assert response_get.status_code == 200

        response_delete = self.simulate_delete("/"+self.API_NAME+"/vocab")
        assert response_delete.status_code == 405

        response_put = self.simulate_put("/"+self.API_NAME+"/vocab", json=dict(foo='bar'))
        assert response_put.status_code == 405

        response_post = self.simulate_post("/"+self.API_NAME+"/vocab", json=dict(foo='bar'))
        assert response_post.status_code == 405

    def test_Collections_GET(self):
        """Test GET on collection endpoints."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_get(endpoints[endpoint])
                # pdb.set_trace()
                assert response_get.status_code == 200
                response_get_data = response_get.json
                assert "@context" in response_get_data
                assert "@id" in response_get_data
                assert "@type" in response_get_data
                assert "members" in response_get_data

    def test_Collections_PUT(self):
        """Test insert data to the collection."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                collection = self.doc.collections[collection_name]["collection"]
                dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                good_response_put = self.simulate_put(endpoints[collection_name], json=dummy_object)
                assert good_response_put.status_code == 201

    def test_object_POST(self):
        """Test replace of a given object using ID."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                collection = self.doc.collections[collection_name]["collection"]
                class_ = self.doc.parsed_classes[collection.class_.title]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                initial_put_response = self.simulate_put(endpoints[collection_name], json=dummy_object)
                assert initial_put_response.status_code == 201
                response = initial_put_response.json
                regex = r'(.*)ID (\d)* (.*)'
                matchObj = re.match(regex, response["message"])
                assert matchObj is not None
                id_ = matchObj.group(2)
                if "POST" in class_methods:
                    dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                    post_replace_response = self.simulate_post(endpoints[collection_name]+'/'+id_, json=dummy_object)
                    assert post_replace_response.status_code == 200

    def test_object_DELETE(self):
        """Test DELETE of a given object using ID."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                collection = self.doc.collections[collection_name]["collection"]
                class_ = self.doc.parsed_classes[collection.class_.title]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                initial_put_response = self.simulate_put(endpoints[collection_name], json=dummy_object)
                assert initial_put_response.status_code == 201
                response = initial_put_response.json
                regex = r'(.*)ID (\d)* (.*)'
                matchObj = re.match(regex, response["message"])
                assert matchObj is not None
                id_ = matchObj.group(2)
                if "DELETE" in class_methods:
                    delete_response = self.simulate_delete(endpoints[collection_name]+'/'+id_)
                    assert delete_response.status_code == 200

    def test_object_PUT_at_id(self):
        """Create object in collection using PUT at specific ID."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                collection = self.doc.collections[collection_name]["collection"]
                class_ = self.doc.parsed_classes[collection.class_.title]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                if "PUT" in class_methods:
                    dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                    put_response = self.simulate_put(endpoints[collection_name]+'/'+str(random.randint(100, 1000)),
                                              json=dummy_object)
                    assert put_response.status_code == 201

    def test_endpointClass_PUT(self):
        """Check non collection Class PUT."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for class_name in endpoints:
            if class_name not in self.doc.collections and class_name not in ["@context", "@id", "@type"]:
                class_ = self.doc.parsed_classes[class_name]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                if "PUT" in class_methods:
                    dummy_object = gen_dummy_object(class_.title, self.doc)
                    put_response = self.simulate_put(endpoints[class_name], json=dummy_object)
                    assert put_response.status_code == 201

    def test_endpointClass_POST(self):
        """Check non collection Class POST."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for class_name in endpoints:
            if class_name not in self.doc.collections and class_name not in ["@context", "@id", "@type"]:
                class_ = self.doc.parsed_classes[class_name]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                if "POST" in class_methods:
                    dummy_object = gen_dummy_object(class_.title, self.doc)
                    put_response = self.simulate_post(endpoints[class_name], json=dummy_object)
                    assert put_response.status_code == 201

    def test_endpointClass_DELETE(self):
        """Check non collection Class DELETE."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for class_name in endpoints:
            if class_name not in self.doc.collections and class_name not in ["@context", "@id", "@type"]:
                class_ = self.doc.parsed_classes[class_name]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                if "DELETE" in class_methods:
                    put_response = self.simulate_delete(endpoints[class_name])
                    assert put_response.status_code == 200

    def test_endpointClass_GET(self):
        """Check non collection Class GET."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for class_name in endpoints:
            if class_name not in self.doc.collections and class_name not in ["@context", "@id", "@type"]:
                class_ = self.doc.parsed_classes[class_name]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                if "GET" in class_methods:
                    response_get = self.simulate_get(endpoints[class_name])
                    assert response_get.status_code in [200, 404]
                    if response_get.status_code == 200:
                        response_get_data = response_get.json
                        assert "@context" in response_get_data
                        assert "@id" in response_get_data
                        assert "@type" in response_get_data

    def test_bad_objects(self):
        """Checks if bad objects are added or not."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                bad_response_put = self.simulate_put(endpoints[collection_name], json=dict(foo='bar'))
                assert bad_response_put.status_code == 400

    def test_bad_requests(self):
        """Checks if bad requests are handled or not."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                collection = self.doc.collections[collection_name]["collection"]
                class_ = self.doc.parsed_classes[collection.class_.title]["class"]
                class_methods = [x.method for x in class_.supportedOperation]
                dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                initial_put_response = self.simulate_put(endpoints[collection_name], json=dummy_object)
                assert initial_put_response.status_code == 201
                response = initial_put_response.json
                regex = r'(.*)ID (\d)* (.*)'
                matchObj = re.match(regex, response["message"])
                assert matchObj is not None
                id_ = matchObj.group(2)
                if "POST" not in class_methods:
                    dummy_object = gen_dummy_object(collection.class_.title, self.doc)
                    post_replace_response = self.simulate_post(endpoints[collection_name]+'/'+id_, json=dummy_object)
                    assert post_replace_response.status_code == 405
                if "DELETE" not in class_methods:
                    delete_response = self.simulate_delete(endpoints[collection_name]+'/'+id_)
                    assert delete_response.status_code == 405

    def test_Endpoints_Contexts(self):
        """Test all endpoints contexts are generated properly."""
        index = self.simulate_get("/"+self.API_NAME)
        assert index.status_code == 200
        endpoints = index.json
        for collection_name in endpoints:
            if collection_name in self.doc.collections:
                response_get = self.simulate_get(endpoints[collection_name])
                assert response_get.status_code == 200
                context = response_get.json["@context"]
                if context:
                    response_context = self.simulate_get(context)
                    response_context_data = response_context.json
                    assert response_context.status_code == 200
                    assert "@context" in response_context_data


if __name__ == '__main__':
    message = """
    Running tests for the app. Checking if all responses are in proper order.
    """
    print(message)
