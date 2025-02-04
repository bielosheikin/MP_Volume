from abc import ABC
import numpy as np
from typing import List, Tuple
from .trackable import Trackable


class HistoriesStorage:
    def __init__(self):
        self.objects = {}
        self.histories = {}
        
    def register_object(self, obj: Trackable):
        assert issubclass(type(obj), Trackable)
        if (obj_name := obj.display_name) in self.objects:
            raise RuntimeError(f'An object with the name {obj_name} has been already registered')
        else:
            self.objects[obj_name] = obj
            for field_name in obj.TRACKABLE_FIELDS:
                if not hasattr(obj, field_name):
                    raise ValueError(f'An error while trying to registed an object {obj_name} with Histories. '
                                      f'The object doesn\'t have {field_name} attribute.')
                self.histories[f'{obj_name}_{field_name}'] = []
        
    def update_histories(self):
        for obj_name, obj in self.objects.items():
            current_state = obj.get_current_state()
            for field_name, field_value in current_state.items():
                self.histories[f'{obj_name}_{field_name}'].append(field_value)
                
    def flush_histories(self):
        for tracked_field_name in self.histories.keys():
            self.histories[tracked_field_name] = []

    def display_histories(self):
        for key, values in self.histories.items():
            print(f"{key}: {values}")
        
    def get_histories(self):
        return self.histories    