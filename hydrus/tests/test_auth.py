"""Try authorization on all possible URIs on the server."""

from hydrus.data.user import generate_basic_digest
import json
import unittest
from hydrus.app import app_factory
from hydrus.utils import Getter_setter
from hydrus.data import doc_parse
from hydrus.hydraspec import doc_writer_sample, doc_maker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from hydrus.data.db_models import Base
from hydrus.data.user import add_user
from base64 import b64encode
from falcon import testing


# response = requests.get("http://127.0.0.1:8080/serverapi/CommandCollection", headers={'Authorization':'Basic QWxhZGRpbjpPcGVuU2VzYW1l'})


class AuthTestCase(testing.TestCase):
    """Test Class for the app."""

    def setUp(self):
        """Database setup before the tests."""
        super(AuthTestCase, self).setUp()
        print("Creating a temporary datatbase...")
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        session = scoped_session(sessionmaker(bind=engine))

        self.session = session
        self.API_NAME = "demoapi"
        self.HYDRUS_SERVER_URL = "http://hydrus.com/"
        self.doc = doc_maker.create_doc(doc_writer_sample.api_doc.generate(), self.HYDRUS_SERVER_URL, self.API_NAME)
        self.gs = Getter_setter(self.session, self.HYDRUS_SERVER_URL, self.API_NAME, self.doc, True)
        self.app = app_factory(self.API_NAME, self.gs)
        test_classes = doc_parse.get_classes(self.doc.generate())
        test_properties = doc_parse.get_all_properties(test_classes)
        doc_parse.insert_classes(test_classes, self.session)
        doc_parse.insert_properties(test_properties, self.session)
        add_user(1, "test", self.session)
        self.auth_header = {"Authorization": "Basic " + b64encode(b"1:test").decode("utf-8")}
        self.wrong_id = {"Authorization": "Basic " + b64encode(b"2:test").decode("utf-8")}
        self.wrong_pass = {"Authorization": "Basic " + b64encode(b"1:test2").decode("utf-8")}
        print("Classes, Properties and Users added successfully.")

        print("Setting up Hydrus utilities... ")
        
        print("Creating utilities context... ")

        print("Setup done, running tests...")


class TestCases(AuthTestCase):

    def test_wrongID_GET(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_get(endpoints[endpoint], headers=self.wrong_id)
                assert response_get.status_code == 401 or response_get.status_code == 400

    def test_wrongID_POST(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_post(endpoints[endpoint], headers=self.wrong_id, json=dict(foo="bar"))
                assert response_get.status_code == 401 or response_get.status_code == 400

    def test_wrongPass_GET(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_get(endpoints[endpoint], headers=self.wrong_pass)
                assert response_get.status_code == 401

    def test_wrongPass_POST(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_post(endpoints[endpoint], headers=self.wrong_pass, json=dict(foo="bar"))
                assert response_get.status_code == 401

    def test_Auth_GET(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_get(endpoints[endpoint], headers=self.auth_header)
                assert response_get.status_code != 401

    def test_Auth_POST(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_post(endpoints[endpoint], headers=self.auth_header, json=dict(foo="bar"))
                assert response_get.status_code != 401

    def test_Auth_PUT(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_put(endpoints[endpoint], headers=self.auth_header, json=dict(foo="bar"))
                assert response_get.status_code != 401

    def test_Auth_DELETE(self):
        """Test for the index."""
        response_get = self.simulate_get("/"+self.API_NAME)
        endpoints = response_get.json
        for endpoint in endpoints:
            if endpoint in self.doc.collections:
                response_get = self.simulate_delete(endpoints[endpoint], headers=self.auth_header)
                assert response_get.status_code != 401


if __name__ == '__main__':
    message = """
    Running tests for authorization. Checking if all responses are in proper order.
    """
    print(message)
    unittest.main()
