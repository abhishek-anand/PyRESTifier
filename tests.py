import json
import unittest
import publishers


class RESTPublisherTestCase(unittest.TestCase):
    """
    Tests for the RESTPublisher Class.
    These tests use the externally defined functions
    for the resource to to published, i.e. users.
    """
    def setUp(self):
        # Creating a RESTPublisher
        rest_publisher = publishers.RESTPublisher()
        mappings = publishers.VerbMappings(get={'method': get_user},
                                           get_all={'method': get_all},
                                           add={'method': add_user},
                                           edit={'method': edit_user},
                                           delete={'method': delete_user},
                                           partial_edit=None)
        rest_publisher.map_resource('users',
                                    mappings,
                                    resource_id=('int', 'id'))
        self.app = rest_publisher.app.test_client()
        # Dummy test users
        self.test_users = [{'email': 'a@bc.com', 'password': 'p'},
                           {'email': 'm@no.com', 'password': 'abc123'}]
        global users  # think of it as a key value datastore ;)
        users = []  # and this as initializing an empty db

    def test_add_user(self):
        """
        Adding a user and then check if the user is added
        """
        self.app.post('/api/users/', data=json.dumps(self.test_users[0]))
        self.assertEqual(users[0]['email'], self.test_users[0]['email'])

    def test_get_user(self):
        """
        Adding a user and then retreiving it via API and matching
        """
        self.app.post('/api/users/', data=json.dumps(self.test_users[0]))
        resp = self.app.get('/api/users/0')
        user0 = json.loads(resp.data)['result']
        self.assertDictEqual(user0, self.test_users[0])

    def test_get_users(self):
        """
        Adding two users and then retreiving the collection and comparing
        """
        self.app.post('/api/users/', data=json.dumps(self.test_users[0]))
        self.app.post('/api/users/', data=json.dumps(self.test_users[1]))
        resp = self.app.get('/api/users/')
        users = json.loads(resp.data)['result']
        self.assertEquals(users, self.test_users)

    def test_edit_user(self):
        """
        Adding a new user and changing their password and verifying
        """
        new_user = {'email': 'eviluser@scroll.in', 'password': 'weakpass'}
        self.app.post('/api/users/', data=json.dumps(new_user))
        self.assertEqual(users[0]['password'], new_user['password'])
        new_password = 'password123'
        new_user['password'] = new_password
        self.app.put('/api/users/0', data=json.dumps(new_user))
        self.assertEqual(users[0]['password'], new_password)

    def test_delete_user(self):
        """
        Delete a user after adding two users.
        These tests might fail as ideally we would be using non-changing
        uuids but here we are using array indices which would change on
        deleting a particular elements and tests would fail.
        """
        self.app.post('/api/users/', data=json.dumps(self.test_users[0]))
        self.app.post('/api/users/', data=json.dumps(self.test_users[1]))
        self.assertEqual(len(users), 2)
        self.app.delete('/api/users/0')
        self.assertEqual(len(users), 1)
        # id of second user changes here, unlike a practical uuid !
        self.assertEqual(self.test_users[1], users[0])


class HTTPPublisherTestCase(unittest.TestCase):
    def setUp(self):
        self.http_publisher = publishers.HTTPPublisher()

    def test_add(self):
        """Map a function to add two numbers and check"""
        self.http_publisher.add_mapping(add)
        app = self.http_publisher.app.test_client()
        resp = app.post('/add/', data=json.dumps({'a': 2, 'b': 3}))
        result = json.loads(resp.data)['result']
        self.assertEqual(result, 5)

    def test_iszero(self):
        """Map a function with custom url to test equality to zero and check"""
        self.http_publisher.add_mapping(is_zero, '/iszero/')  # mapping custom url 
        app = self.http_publisher.app.test_client()
        resp = app.post('/iszero/', data=json.dumps({'n': 3}))
        result = json.loads(resp.data)['result']
        self.assertFalse(result)


# The User Resource
users = []
PAGE_SIZE = 10


def add_user(email, password):
    user = dict(email=email, password=password)
    users.append(user)
    return users.index(user)


def edit_user(id, email=None, password=None):
    if email is not None:
        users[id]['email'] = email
    if password is not None:
        users[id]['password'] = password
    return True


def get_user(id):
    return users[id]


def get_all(page_no=1):
    return users[PAGE_SIZE*(page_no-1):PAGE_SIZE*(page_no)]


def delete_user(id):
    users.pop(id)
    return True


def is_zero(n):
    return n == 0


def add(a, b):
    return a + b


if __name__ == '__main__':
    unittest.main()
