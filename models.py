__author__ = 'sweemeng'
"""
This is currently a hack, a prototype which we will move and shuffle around. The big idea is

* do everything via API call. popit api is pretty complete after all
* add missing feature in UI, for example
  * adding new post
  * adding new post while creating user
"""
import requests

# Yeah a little silly, but nice for autocomplete
ORGANIZATIONS = "organizations"
PERSONS = "persons"
MEMBERSHIPS = "memberships"
POSTS = "posts"

# TODO: Possibly a good idea to think of a cache here
class PopitProxy(object):
    def __init__(self, entity, url="https://sinar-malaysia.popit.mysociety.org/api", version="v0.1", language="en", api_key=""):
        """
        :param url: url of popit API instance,
        :param entity: support only person, organization, posts
        :param version: support API version
        :param language: language version
        :param api_key: only needed for update
        :return:
        """
        if version:
            self.url = "%s/%s/%s" % (url, version, entity)
        else:
            self.url = "%s/%s" % (url, entity)

        # individual language for now,
        self.header = {
            "Accept-Language": language,
            #"Accept": "application/json",
            #"Content-Type": "application/json"
        }
        if api_key:
            self.header["Apikey"] = api_key

    def list_all(self):
        r = requests.get(self.url, headers=self.header)
        entities = r.json()
        # TODO: I am not sure if we should return all or ID only
        return entities

    def get(self, entity_id):
        """
        :param entity_id: uuid for entity on popit
        :return:
        """
        entity_url = "%s/%s" % (self.url, entity_id)
        r = requests.get(entity_url, headers=self.header)
        return r.json()

    def update(self, entity_id, field_updated, value):
        """
        :param entity_id: i
        :param field_updated:
        :param value:
        :return:

        Request only update necessary field, but not all field.
        """
        data = { field_updated: value}
        url = "%s/%s" % (self.url, entity_id)
        r = requests.put(url, data=data)
        # TODO: handle r.status_code
        return r.json()

    def create(self, data):
        r = requests.post(self.url, data=data, headers=self.header)
        # TODO: handle r.status_code
        return r.json()

    def delete(self, entity_id):
        r = requests.delete(self.url, headers=self.header)