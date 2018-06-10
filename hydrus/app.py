"""Main route for the applciation."""

import json
import falcon
from hydrus.data import crud
from hydrus.data.user import check_authorization
from hydrus.utils import get_doc, get_api_name, get_authentication, get_hydrus_server_url, get_session
from hydrus.hydraspec import doc_writer_sample
from typing import Dict, List, Any, Union





def validObject(object_: Dict[str, Any]) -> bool:
    """Check if the data passed in POST is of valid format or not."""
    if "@type" in object_:
        return True
    return False


def failed_authentication(resp: falcon.Response):
    """Return failed authentication object."""
    resp.status = falcon.HTTP_401
    resp = set_response_headers(resp,
                                    headers={'WWW-Authenticate': 'Basic realm="Login Required"'}, status_code=falcon.HTTP_401)


def set_response_headers(resp: falcon.Response, ct: str="application/ld+json", headers: Dict[str, Any]={}, status_code = falcon.HTTP_200) -> falcon.Response:
    resp.status = status_code
    resp.set_headers(headers)
    resp.set_header('Content-type', ct)
    resp.set_header('Link' ,'<' + get_hydrus_server_url(resp) + \
        get_api_name(resp)+'/vocab>; rel="http://www.w3.org/ns/hydra/core#apiDocumentation"')
    return resp


# def set_response_headers(resp: Response, ct: str="application/ld+json", headers: List[Dict[str, Any]]=[], status_code = falcon.HTTP_200) -> Response:
#
#     resp.status_code = status_code
#     for header in headers:
#         resp.headers[list(header.keys())[0]] = header[list(header.keys())[0]]
#     resp.headers['Content-type'] = ct
#     resp.headers['Link'] = '<' + get_hydrus_server_url() + \
#         get_api_name()+'/vocab>; rel="http://www.w3.org/ns/hydra/core#apiDocumentation"'
#     return resp



def hydrafy(resp: falcon.Response,object_: Dict[str, Any]) -> Dict[str, Any]:
    """Add hydra context to objects."""
    object_["@context"] = "/"+ get_api_name(resp) +"/contexts/" + object_["@type"] + ".jsonld"
    return object_

def checkEndpoint(resp: falcon.Response, method: str, type_: str) -> Dict[str, Union[bool, falcon.HTTPStatus]]:
    """Check if endpoint and method is supported in the API."""
    status_code = falcon.HTTP_404
    if type_ == 'vocab':
        return {'method': False, 'status': falcon.HTTP_405}

    for endpoint in get_doc(resp).entrypoint.entrypoint.supportedProperty:
        if type_ == endpoint.name:
            status_code = falcon.HTTP_405
            for operation in endpoint.supportedOperation:
                if operation.method == method:
                    status_code = falcon.HTTP_200
                    return {'method': True, 'status': status_code}
    return {'method': False, 'status': status_code}


def getType(resp: falcon.Response, class_type: str, method: str) -> Any:
    """Return the @type of object allowed for POST/PUT."""
    for supportedOp in get_doc(resp).parsed_classes[class_type]["class"].supportedOperation:
        if supportedOp.method == method:
            return supportedOp.expects.replace("vocab:", "")
    # NOTE: Don't use split, if there are more than one substrings with 'vocab:' not everything will be returned.


def checkClassOp(resp: falcon.Response, class_type: str, method: str) -> bool:
    """Check if the Class supports the operation."""
    for supportedOp in get_doc(resp).parsed_classes[class_type]["class"].supportedOperation:
        if supportedOp.method == method:
            return True
    return False



class Index(object):
    """Class for the EntryPoint."""

    def on_get(self, req, resp):
        """Return main entrypoint for the api."""
        resp.media = get_doc(resp).entrypoint.get()
        resp = set_response_headers(resp)



class Vocab(object):
    """Vocabulary for Hydra."""

    def on_get(self, req, resp):
        """Return the main hydra vocab."""
        resp.media = get_doc(resp).generate()
        resp = set_response_headers(resp)


class Entrypoint(object):
    """Hydra EntryPoint."""

    def on_get(self, req, resp):
        """Return application main Entrypoint."""
        resp.media = {"@context": get_doc(resp).entrypoint.context.generate()}
        resp = set_response_headers(resp)

class Item(object):
    """Handles all operations(GET, POST, PATCH, DELETE) on Items (item can be anything depending upon the vocabulary)."""

    def on_get(self, req, resp, id_, type_):
        """GET object with id = id_ from the database."""

        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        class_type = get_doc(resp).collections[type_]["collection"].class_.title

        if checkClassOp(resp, class_type, "GET"):

            try:
                resp.media = hydrafy(resp, crud.get(id_, class_type, api_name=get_api_name(resp), session=get_session(resp)))
                return set_response_headers(resp)

            except Exception as e:
                status_code, message = e.get_HTTP()
                resp.media = message
                return set_response_headers(resp, status_code= status_code)

        resp.status = falcon.HTTP_405

    def on_post(self, req, resp, id_: int, type_: str):
        """Update object of type<type_> at ID<id_> with new object_ using HTTP POST.

        :param id_ - ID of Item to be updated
        :param type_ - Type(Class name) of Item to be updated
        """
        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        class_type = get_doc(resp).collections[type_]["collection"].class_.title

        if checkClassOp(resp, class_type, "POST"):
            # Check if class_type supports POST operation
            object_ = req.media
            obj_type = getType(resp, class_type, "POST")
            # Load new object and type
            if validObject(object_):
                if object_["@type"] == obj_type:
                    try:
                        # Update the right ID if the object is valid and matches
                        # type of Item
                        object_id = crud.update(object_=object_, id_=id_, type_=object_[
                                                "@type"], session=get_session(resp), api_name=get_api_name(resp))
                        headers_ = [{"Location": get_hydrus_server_url(resp
                        ) + get_api_name(resp) + "/" + type_ + "/" + str(object_id)}]
                        response = {
                            "message": "Object with ID %s successfully updated" % (object_id)}
                        resp.media = response
                        return set_response_headers(resp, headers=headers_[0])
                    except Exception as e:
                        status_code, message = e.get_HTTP()
                        resp.media = message
                        return set_response_headers(resp, status_code)

            return set_response_headers(resp, status_code= falcon.HTTP_400)

        resp.status = falcon.HTTP_405


    def on_put(self, req, resp, id_: int, type_: str):
        """Add new object_ optional <id_> parameter using HTTP PUT.

        :param id_ - ID of Item to be updated
        :param type_ - Type(Class name) of Item to be updated
        """
        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        class_type = get_doc(resp).collections[type_]["collection"].class_.title

        if checkClassOp(resp, class_type, "PUT"):
            # Check if class_type supports PUT operation
            object_ = req.media
            obj_type = getType(resp, class_type, "PUT")
            # Load new object and type
            if validObject(object_):
                if object_["@type"] == obj_type:
                    try:
                        # Add the object with given ID
                        object_id = crud.insert(
                            object_=object_, id_=id_, session=get_session(resp))
                        headers_ = [{"Location": get_hydrus_server_url(resp
                        ) + get_api_name(resp) + "/" + type_ + "/" + str(object_id)}]
                        response = {
                            "message": "Object with ID %s successfully added" % (object_id)}
                        resp.media = response
                        return set_response_headers(resp, headers=headers_[0], status_code= falcon.HTTP_201)
                    except Exception as e:
                        status_code, message = e.get_HTTP()
                        resp.media = message
                        return set_response_headers(resp, status_code=status_code)

            return set_response_headers(resp, status_code=falcon.HTTP_400)

        resp.status = falcon.HTTP_405


    def on_delete(self, req, resp, id_: int, type_: str):
        """Delete object with id=id_ from database."""

        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        class_type = get_doc(resp).collections[type_]["collection"].class_.title

        if checkClassOp(resp, class_type, "DELETE"):
            # Check if class_type supports PUT operation
            try:
                # Delete the Item with ID == id_
                crud.delete(id_, class_type, session=get_session(resp))
                response = {
                    "message": "Object with ID %s successfully deleted" % (id_)}
                resp.media = response
                return set_response_headers(resp)

            except Exception as e:
                status_code, message = e.get_HTTP()
                resp.media = message
                return set_response_headers(resp, status_code= status_code)

        resp.status = falcon.HTTP_405




class ItemCollection(object):
    """Handle operation related to ItemCollection (a collection of items)."""

    def on_get(self, req, resp, type_):
        """Retrieve a collection of items from the database."""
        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        if checkEndpoint(resp, "GET", type_):
            # Collections
            if type_ in get_doc(resp).collections:

                collection = get_doc(resp).collections[type_]["collection"]
                try:
                    resp.media = crud.get_collection(get_api_name(resp), collection.class_.title, session=get_session(resp))
                    return set_response_headers(resp)

                except Exception as e:
                    status_code, message = e.get_HTTP()
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

            # Non Collection classes
            elif type_ in get_doc(resp).parsed_classes and type_+"Collection" not in get_doc(resp).collections:
                try:
                    resp.media = hydrafy(resp, crud.get_single(type_, api_name=get_api_name(resp), session=get_session(resp)))
                    return set_response_headers(resp)

                except Exception as e:
                    status_code, message = e.get_HTTP()
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

    def on_put(self, req, resp, type_: str):
        """
        Method executed for PUT requests.
        Used to add an item to a collection

        :param type_ - Item type
        """
        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        endpoint_ = checkEndpoint(resp, "PUT", type_)
        if endpoint_['method']:
            # If endpoint and PUT method is supported in the API
            object_ = req.media

            if type_ in get_doc(resp).collections:
                # If collection name in document's collections
                collection = get_doc(resp).collections[type_]["collection"]

                # title of HydraClass object corresponding to collection
                obj_type = collection.class_.title

                if validObject(object_):
                    # If Item in request's JSON is a valid object
                    # ie. @type is one of the keys in object_
                    if object_["@type"] == obj_type:
                        # If the right Item type is being added to the collection
                        try:
                            # Insert object and return location in Header
                            object_id = crud.insert(
                                object_=object_, session=get_session(resp))
                            headers_ = [{"Location": get_hydrus_server_url(resp
                            ) + get_api_name(resp) + "/" + type_ + "/" + str(object_id)}]
                            response = {
                                "message": "Object with ID %s successfully added" % (object_id)}
                            resp.media = response
                            return set_response_headers(resp, headers=headers_[0], status_code=falcon.HTTP_201)
                        except Exception as e:
                            status_code, message = e.get_HTTP()
                            resp.media = message
                            return set_response_headers(resp, status_code=status_code)

                return set_response_headers(resp, status_code=falcon.HTTP_400)

            elif type_ in get_doc(resp).parsed_classes and type_ + "Collection" not in get_doc(resp).collections:
                # If type_ is in parsed_classes but is not a collection
                obj_type = getType(resp, type_, "PUT")
                if object_["@type"] == obj_type:
                    if validObject(object_):
                        try:
                            object_id = crud.insert(
                                object_=object_, session=get_session(resp))
                            headers_ = [{"Location": get_hydrus_server_url(resp
                            ) + get_api_name(resp) + "/" + type_ + "/"}]
                            response = {"message": "Object successfully added"}
                            resp.media = response
                            return set_response_headers(resp, headers=headers_[0], status_code=falcon.HTTP_201)
                        except Exception as e:
                            status_code, message = e.get_HTTP()
                            resp.media = message
                            return set_response_headers(resp, status_code=status_code)

                return set_response_headers(resp, status_code=falcon.HTTP_400)


    def on_post(self, req, resp, type_: str):
        """
        Method executed for POST requests.
        Used to update a non-collection class.

        :param type_ - Item type
        """
        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        endpoint_ = checkEndpoint(resp, "POST", type_)
        if endpoint_['method']:
            object_ = req.media
            if type_ in get_doc(resp).parsed_classes and type_ + "Collection" not in get_doc(resp).collections:
                obj_type = getType(resp, type_, "POST")
                if validObject(object_):
                    if object_["@type"] == obj_type:
                        try:
                            crud.update_single(
                                object_=object_, session=get_session(resp), api_name=get_api_name(resp))
                            headers_ = [{"Location": get_hydrus_server_url(resp
                            ) + get_api_name(resp) + "/" + type_ + "/"}]
                            response = {"message": "Object successfully updated"}
                            resp.media = response
                            return set_response_headers(resp, headers=headers_[0])
                        except Exception as e:
                            status_code, message = e.get_HTTP()
                            resp.media = message
                            return set_response_headers(resp, status_code=status_code)

                return set_response_headers(resp, status_code=falcon.HTTP_400)



    def on_delete(self, req, resp, type_: str):
        """
        Method executed for DELETE requests.
        Used to delete a non-collection class.

        :param type_ - Item type
        """
        if get_authentication(resp):
            if req.auth is None:
                return failed_authentication(resp)
            else:
                try:
                    auth = check_authorization(req, get_session(resp))
                    if auth is False:
                        return failed_authentication(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()  # type: ignore
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)

        endpoint_ = checkEndpoint(resp, "DELETE", type_)
        if endpoint_['method']:
            # No Delete Operation for collections
            if type_ in get_doc(resp).parsed_classes and type_ + "Collection" not in get_doc(resp).collections:
                try:
                    crud.delete_single(type_, session=get_session(resp))
                    response = {"message": "Object successfully deleted"}
                    resp.media = response
                    return set_response_headers(resp)
                except Exception as e:
                    status_code, message = e.get_HTTP()
                    resp.media = message
                    return set_response_headers(resp, status_code=status_code)


class Contexts(object):
    """Dynamically genereated contexts."""

    def on_get(self, req, resp, category: str) -> falcon.Response:
        """Return the context for the specified class."""
        if "Collection" in category:

            if category in get_doc(resp).collections:
                resp.media = {"@context": get_doc(resp).collections[category]["context"].generate()} # type: Union[Dict[str,Any],Dict[int,str]]
                return set_response_headers(resp)

            else:
                return set_response_headers(resp, status_code= falcon.HTTP_404)

        else:
            if category in get_doc(resp).parsed_classes:
                resp.media = {"@context": get_doc(resp).parsed_classes[category]["context"].generate()}
                return set_response_headers(resp)

            else:
                return set_response_headers(resp, status_code=falcon.HTTP_404)


def app_factory(API_NAME: str, gsm) -> falcon.API:
    """Create an app object."""

    api = falcon.API(middleware=[gsm])

    api.add_route("/"+API_NAME+"/",Index())
    api.add_route("/" + API_NAME + "/vocab", Vocab())
    api.add_route("/"+API_NAME+"/contexts/{category}"+".jsonld", Contexts())
    api.add_route("/"+API_NAME+"/contexts/EntryPoint.jsonld",Entrypoint())
    api.add_route("/"+API_NAME+"/{type_}", ItemCollection())
    api.add_route("/"+API_NAME+"/{type_}/{id_:int()}", Item())

    return api

