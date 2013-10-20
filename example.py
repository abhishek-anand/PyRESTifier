# -*- coding: utf-8 -*-
"""
An example of using RESTPublisher and HTTPPublisher
We would publish a REST API for ToDo List, two maths functions and a python
library function as remote calls over HTTP, all over the same location (port).
"""
import publishers
import md5


def is_zero(n):
    return n == 0


def add(a, b):
    return a + b


# A resource ToDos would be mapped to a REST API using its class methods
# Note that the methods can do any complex operations inside them
class ToDoList(object):
    def __init__(self):
        self.todos = []

    def add_todo(self, item):
        self.todos.append(item)
        return True

    def get_all_todos(self):
        return self.todos

    def get_todo(self, index):
        try:
            return self.todos[index]
        except IndexError:
            return ''

    def mark_complete(self, index):  # yes we delete completed items here ;)
        try:
            self.todos.pop(index)
            return True
        except IndexError:
            return False

    def edit_todo(self, index, item):
        try:
            self.todos[index] = item
            return True
        except IndexError:
            return False

todo_list = ToDoList()

# An object that stores the mappings between your callables and required
# operations to implement the REST API
mapping = publishers.VerbMappings(get={'method': todo_list.get_todo},
                                  get_all={'method': todo_list.get_all_todos},
                                  add={'method': todo_list.add_todo},
                                  edit={'method': todo_list.edit_todo},
                                  delete={'method': todo_list.mark_complete},
                                  partial_edit=None)


# Publishing the math functions add and is_zero as normal HTTP remote calls
http_publisher = publishers.HTTPPublisher()
http_publisher.add_mapping(add)
http_publisher.add_mapping(is_zero, '/iszero/')  # custom defined url
http_publisher.add_mapping(lambda x: md5.md5(*[x]).hexdigest(), '/checksum/')

# Here we are using the same app created for HTTPPublisher, we could in fact
# have created a new flask app here and passed it to both of these as parameter
# but this was just to demonstrate that creating a flask app explicitly is
# really not required if you just want to publish your api for a module
rest_publisher = publishers.RESTPublisher(http_publisher.app)
rest_publisher.map_resource('todos', mapping, ('int', 'index'))
# You can map several resources using  single rest_publisher


if __name__ == "__main__":
    # to publish the API on a particular port, you could pass the port as
    # a parameter to publish, otherwise it will start on a random port which
    # you can check via the console logs
    rest_publisher.publish()  # http_publisher gets auto published as they share app instance
    