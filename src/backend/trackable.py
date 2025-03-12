from abc import ABC, abstractmethod
from typing import Tuple


class Trackable:
    """
    A base class for objects that can be tracked over time.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize a trackable object.
        
        Args:
            **kwargs: Keyword arguments, including display_name if provided directly
        """
        # display_name will be set by Configurable if it's a config field,
        # otherwise we need to set it from kwargs or raise an error
        if not hasattr(self, 'display_name'):
            if 'display_name' not in kwargs:
                raise ValueError("display_name must be provided either as a config field or as an argument")
            self.display_name = kwargs['display_name']

    @property
    def TRACKABLE_FIELDS(self) -> Tuple[str, ...]:
        """
        Returns a tuple of field names that should be tracked over time.
        """
        raise NotImplementedError("Subclasses must define TRACKABLE_FIELDS")

    def get_current_state(self) -> dict:
        """
        Get the current state of the object based on its TRACKABLE_FIELDS.
        
        Returns:
            dict: A dictionary mapping field names to their current values.
        """
        return {field: getattr(self, field) for field in self.TRACKABLE_FIELDS}
        