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
            # Check if the existing object is of the same type
            existing_obj = self.objects[obj_name]
            if type(existing_obj) == type(obj):
                object_type = type(obj).__name__
                raise RuntimeError(f'Duplicate {object_type}: An object with the name "{obj_name}" has already been registered.')
            else:
                existing_type = type(existing_obj).__name__
                new_type = type(obj).__name__
                raise RuntimeError(f'Name conflict: "{obj_name}" is already used by a {existing_type}, cannot use it for a {new_type}. Please ensure all objects have unique names.')
        else:
            self.objects[obj_name] = obj
            for field_name in obj.TRACKABLE_FIELDS:
                if not hasattr(obj, field_name):
                    raise ValueError(f'An error while trying to register an object "{obj_name}" with Histories. '
                                     f'The object doesn\'t have the "{field_name}" attribute.')
                self.histories[f'{obj_name}_{field_name}'] = []
        
    def update_histories(self):
        for obj_name, obj in self.objects.items():
            current_state = obj.get_current_state()
            for field_name, field_value in current_state.items():
                self.histories[f'{obj_name}_{field_name}'].append(field_value)
                
    def flush_histories(self):
        for tracked_field_name in self.histories.keys():
            self.histories[tracked_field_name] = []

    def reset(self):
        """Reset the storage to its initial state, clearing all objects and histories."""
        self.objects = {}
        self.histories = {}

    def display_histories(self):
        """Display histories in a structured format (for debugging only)."""
        # This method is only for debugging and doesn't need to print to terminal
        return {key: len(values) for key, values in self.histories.items()}
        
    def get_histories(self):
        return self.histories    