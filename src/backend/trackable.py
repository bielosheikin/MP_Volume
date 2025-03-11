from abc import ABC, abstractmethod
from typing import Tuple


class Trackable:
    """
    A base class for objects that can be tracked over time.
    """
    
    def __init__(self, display_name: str):
        """
        Initialize a trackable object.
        
        Args:
            display_name (str): The name to display for this object in plots and output.
        """
        self.display_name = display_name

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
        