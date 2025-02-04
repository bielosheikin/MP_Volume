from abc import ABC
from typing import List, Tuple

class Trackable(ABC):
    TRACKABLE_FIELDS = ()
    
    def __init__(self, 
                 *args,
                 display_name: str = None,
                 trackable_fields: Tuple = None):
        if display_name is None:
            raise ValueError(f'A display_name should be specified when creating a Trackable object')
        self.display_name = display_name
        
        assert isinstance(self.TRACKABLE_FIELDS, tuple)
        assert len(self.TRACKABLE_FIELDS) > 0
        
    def get_current_state(self):
        current_state = {}
        for field_name in self.TRACKABLE_FIELDS:
            current_state[field_name] = getattr(self, field_name)
            
        return current_state
        