"""
Publishers allow you to expose your python callables over HTTP.
The callables can be exposed as a REST API if the group of callables support
CRUD operations over some resource or as generic remote procedure calls.
"""

from collections import namedtuple
from functools import wraps
import random
import json
from flask import Flask, abort, request, jsonify

"""
named tuple to represent mappings between resource
operations and their respective methods, uuids etc.
callables: can be
            - object with http verbs as method names
                class Todos:
                    def get():
                    def post():
                class Todo:
                    def get():
                    def post():
                    def delete():
                todo_collection = Todos()
                todo_resource = Todo()
All tuple elements would map to a dictionary which would
contain information like method i.e. a callable to be called,
authentication method and schema if any.
"""
VerbMappings = namedtuple('verb_mappings', ['add',
                                            'get',
                                            'get_all',
                                            'edit',
                                            'partial_edit',
                                            'delete'])


class Publisher(object):
    """
    An API publisher that uses flask, a python web micro-framework.
    callables can be published using RESTPublisher if they are for a resource
    or as remote procedure calls over HTTP using the HTTPPublisher.

    By default the publisher uses an inbuilt json serializer for results and
    taking json data in requests. You could change it to something else but
    then you would have to supply a callable to the parameter wrapper
    """
    def __init__(self, api_urls_prefix, flask_app=None,
                 serializer='json', wrapper=None):
        if flask_app is not None:
            self.app = flask_app
        else:
            self.app = Flask(__name__)
        self.urls_prefix = api_urls_prefix
        self.serializer = serializer
        self.wrapper = wrapper

    def get_mappings(self):
        """Returns a custom Map of list of urls to callable mappings"""
        return self.app.url_map

    def publish(self, debug=False, port=random.randint(8000, 9999)):
        # TODO: Log
        print 'API Mappings :'
        print self.get_mappings()
        print
        print 'Publishing the API on port %d' % port
        self.app.run(debug=debug, port=port)

    def wrap(self, f):
        """
        Serializes output to JSON.
        Wrapper is a helper function helping in serializing and
        de-serializing of results and input parameters respectively.
        You could swap this particualar wrapper with some other
        one, say with XML serialization.
        """
        @wraps(f)
        def json_wrapper(*args, **kw):
            kw.update(request.json
                      or (request.data and json.loads(request.data)) or {})
            try:
                result = f(*args, **kw)
                return jsonify(result=result)
            except Exception as err:
                # TODO: log
                print(err)
                abort(500)
        if self.serializer == 'json':
            return json_wrapper
        else:
            return self.wrapper


class RESTPublisher(Publisher):
    """
    Expose a generic Python module as a RESTful service.
    This uses Flask, a micro-framework to expose required methods/functions.
    Current implementation does not implement partial edit or support for
    HTTP PATCH.

    A module which has to be exposed as a REST service should ideally be
    implemented as follows -

    Each resource should have
    a method to get resource accepting a single parameter
    a method to create the resource and a unique id
    a method to list all created resources
    a method to take a single parameter and delete a resource
    """
    def __init__(self, flask_app=None, api_urls_prefix='/api',
                 serializer='json', wrapper=None):
        """
        Initialized with an instance of flask app, uuid_type and api url prefix
        uuid_type denotes the type used by the resource as uuid
        e.g. int or str
        """
        super(RESTPublisher, self).__init__(api_urls_prefix, flask_app,
                                            serializer, wrapper)
        self.uuid_types = {}

    def map_resource(self, resource_name, mappings, resource_id=('string',
                                                                 'id')):
        """
        Maps a resource and its methods to URLs.
        All mappings are not required and may be passed as None
        A mappings is a named tuple with each value being a dictionary
        """
        self.uuid_types[resource_name] = resource_id[0]
        base_url = ''.join([self.urls_prefix, '/', str(resource_name), '/'])
        get_collections_url = base_url

        resource_url = ''.join([base_url,
                                '<', self.uuid_types[resource_name], ':',
                                resource_id[1], '>'])

        self.app.add_url_rule(resource_url,
                              mappings.get['method'].func_name,
                              self.wrap(mappings.get['method']),
                              methods=['GET'])
        self.app.add_url_rule(get_collections_url,
                              mappings.get_all['method'].func_name,
                              self.wrap(mappings.get_all['method']),
                              methods=['GET'])
        self.app.add_url_rule(base_url,
                              mappings.add['method'].func_name,
                              self.wrap(mappings.add['method']),
                              methods=['POST'])
        self.app.add_url_rule(resource_url,
                              mappings.edit['method'].func_name,
                              self.wrap(mappings.edit['method']),
                              methods=['PUT'])
        self.app.add_url_rule(resource_url,
                              mappings.delete['method'].func_name,
                              self.wrap(mappings.delete['method']),
                              methods=['DELETE'])


class HTTPPublisher(Publisher):
    """
    Expose some generic python methods or functions over HTTP.
    """
    def __init__(self, api_urls_prefix='', flask_app=None,
                 serializer='json', wrapper=None):
        super(HTTPPublisher, self).__init__(api_urls_prefix, flask_app,
                                            serializer, wrapper)

    def add_mapping(self, method, url=None):
        """
        Add a mapping for a method/function.
        If no url is passed, the method is mapped to a url with
        name of the function/method itself.
        """
        if url is None:
            url = ''.join([self.urls_prefix, '/', method.func_name, '/'])
        self.app.add_url_rule(url,
                              method.func_name,
                              self.wrap(method),
                              methods=['POST'])
