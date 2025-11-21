import sys, os
import math
import random
import time
import datetime
import functools

from collections import defaultdict

class EntityRegistry:

    def __init__(self):
        self.by_name = {}
        self.by_tag = defaultdict(set)
        self.name_tags = {}


    def register_entity(self, entity_class):
        name = entity_class.__name__
        tags = entity_class.track_as
        parents = set()
        for parent in entity_class.__mro__:
            pname = parent.__name__
            parents.add(pname)
            if pname == 'Entity':
                break

        if name in self.by_name.keys():
            print(f'!!entity {name} already registered!!')

        self.by_name[name] = entity_class
        self.name_tags[name] = tags|parents|{name}
        for tag in self.name_tags[name]:
            self.by_tag[tag].add(entity_class)


    def create_entity(self, name, app, *args, **kwargs):
        result = self.by_name[name](app, *args, **kwargs)
        return result

entity_registry = EntityRegistry()


def register(cls):
    entity_registry.register_entity(cls)
    return cls

