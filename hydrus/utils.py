"""Pluggable utilities for Hydrus."""


from hydrus.hydraspec import doc_writer_sample
from hydrus.data.db_models import engine
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.orm.session import Session
from hydrus.hydraspec.doc_writer import HydraDoc
import falcon
from typing import Any, Iterator


class Getter_setter(object):
    def __init__(self, db_session, hydrus_server_url: str, api_name, api_doc: HydraDoc, authentication: bool):
        self.db_session = db_session
        self.hydrus_server_url = hydrus_server_url
        self.api_name = api_name
        self.api_doc = api_doc
        self.authentication = authentication

    def process_request(self, req, resp):
        resp.context['db_session'] = self.db_session()
        resp.context['hydrus_server_url'] = self.hydrus_server_url
        resp.context['api_name'] = self.api_name
        resp.context['api_doc'] = self.api_doc
        resp.context['authentication'] = self.authentication



def get_doc(resp):
    try:
        apidoc = resp.context['api_doc']
    except KeyError:
        apidoc = resp.context['api_doc'] = doc_writer_sample.api_doc
    return apidoc

def get_authentication(resp) -> bool:
    """Check wether API needs to be authenticated or not."""
    try:
        authentication = resp.context['authentication']
    except KeyError:
        authentication = resp.context['authentication'] = False
    return authentication

def get_api_name(resp) -> str:
    """Get the server API name."""
    try:
        api_name = resp.context['api_name']
    except KeyError:
        api_name = resp.context['api_name'] = "api"
    return api_name

def get_hydrus_server_url(resp) -> str:
    """Get the server URL."""
    try:
        hydrus_server_url = resp.context['hydrus_server_url']
    except KeyError:
        hydrus_server_url= resp.context['hydrus_server_url'] = "http://localhost/"

    return hydrus_server_url

def get_session(resp) -> Session:
    """Get the Database Session for the server."""
    try:
        session = resp.context['db_session']
    except KeyError:
        session = scoped_session(sessionmaker(bind=engine))
        session = resp.context['db_session'] = session()
    return session



# @contextmanager
# def set_session(application: Flask, DB_SESSION: Session) -> Iterator:
#     """Set the database session for the app. Must be of type <hydrus.hydraspec.doc_writer.HydraDoc>."""
#     if not isinstance(DB_SESSION, Session) and not isinstance(DB_SESSION,scoped_session):
#         raise TypeError("The API Doc is not of type <sqlalchemy.orm.session.Session> or <sqlalchemy.orm.scoping.scoped_session>")
#
#     def handler(sender: Flask, **kwargs: Any) -> None:
#         g.dbsession = DB_SESSION
#     with appcontext_pushed.connected_to(handler, application):
#         yield
#
#
# @contextmanager
# def set_hydrus_server_url(application: Flask, server_url: str) -> Iterator:
#     """Set the server URL for the app. Must be of type <str>."""
#     if not isinstance(server_url, str):
#         raise TypeError("The server_url is not of type <str>")
#
#     def handler(sender: Flask, **kwargs: Any) -> None:
#         g.hydrus_server_url = server_url
#     with appcontext_pushed.connected_to(handler, application):
#         yield
#
#
# @contextmanager
# def set_api_name(application: Flask, api_name: str) -> Iterator:
#     """Set the server name or EntryPoint for the app. Must be of type <str>."""
#     if not isinstance(api_name, str):
#         raise TypeError("The api_name is not of type <str>")
#
#     def handler(sender: Flask, **kwargs: Any) -> None:
#         g.api_name = api_name
#     with appcontext_pushed.connected_to(handler, application):
#         yield
#
#
# @contextmanager
# def set_doc(application: Flask, APIDOC: HydraDoc) -> Iterator:
#     """Set the API Documentation for the app. Must be of type <hydrus.hydraspec.doc_writer.HydraDoc>."""
#     if not isinstance(APIDOC, HydraDoc):
#         raise TypeError("The API Doc is not of type <hydrus.hydraspec.doc_writer.HydraDoc>")
#
#     def handler(sender: Flask, **kwargs: Any) -> None:
#         g.doc = APIDOC
#     with appcontext_pushed.connected_to(handler, application):
#         yield
#
#
# @contextmanager
# def set_authentication(application: Flask, authentication: bool) -> Iterator:
#     """Set the wether API needs to be authenticated or not."""
#     if not isinstance(authentication, bool):
#         raise TypeError("Authentication flag must be of type <bool>")
#
#     def handler(sender: Flask, **kwargs: Any) -> None:
#         g.authentication_ = authentication
#     with appcontext_pushed.connected_to(handler, application):
#         yield
#
#
# def get_doc() -> HydraDoc:
#     """Get the server API Documentation."""
#     apidoc = getattr(g, 'doc', None)
#     if apidoc is None:
#         apidoc = doc_writer_sample.api_doc
#         g.doc = apidoc
#     return apidoc
#

# def get_authentication() -> bool:
#     """Check wether API needs to be authenticated or not."""
#     authentication = getattr(g, 'authentication_', None)
#     if authentication is None:
#         authentication = False
#         g.authentication_ = authentication
#     return authentication
#
#
# def get_api_name() -> str:
#     """Get the server API name."""
#     api_name = getattr(g, 'api_name', None)
#     if api_name is None:
#         api_name = "api"
#         g.doc = api_name
#     return api_name
#
#
# def get_hydrus_server_url() -> str:
#     """Get the server URL."""
#     hydrus_server_url = getattr(g, 'hydrus_server_url', None)
#     if hydrus_server_url is None:
#         hydrus_server_url = "http://localhost/"
#         g.hydrus_server_url = hydrus_server_url
#     return hydrus_server_url
#
#
# def get_session() -> Session:
#     """Get the Database Session for the server."""
#     session = getattr(g, 'dbsession', None)
#     if session is None:
#         session = scoped_session(sessionmaker(bind=engine))
#         g.dbsession = session
#     return session
