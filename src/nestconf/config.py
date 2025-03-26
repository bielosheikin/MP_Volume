import os
import json
import hashlib
import inspect

from abc import ABC


class Config(ABC):
    """
    Base configuration class with utility methods.
    """
    def __getstate__(self):
        """
        Return state for pickling - this ensures all attributes are included.
        """
        return self.__dict__
        
    def __setstate__(self, state):
        """
        Restore state when unpickling.
        """
        self.__dict__ = state
        
    def to_dict(self):
        """
        Convert the configuration to a dictionary, recursively processing
        nested configs, dictionaries, and other complex objects.
        """
        result = {}
        for attr_name in self.__dict__.keys():
            attr_value = getattr(self, attr_name)
            result[attr_name] = self._process_value_for_dict(attr_value)
        
        return result
    
    def _process_value_for_dict(self, value):
        """
        Helper method to recursively process values for dictionary conversion.
        Handles nested configs, dictionaries, lists, and other complex objects.
        """
        # Config objects with to_dict method
        if hasattr(value, 'config') and hasattr(value.config, 'to_dict'):
            # This is a Configurable object with a nested config
            return value.config.to_dict()
        elif hasattr(value, 'to_dict') and callable(value.to_dict):
            # This is an object with a to_dict method (like Config)
            return value.to_dict()
        
        # Dictionary handling - process each key-value pair recursively
        elif isinstance(value, dict):
            return {k: self._process_value_for_dict(v) for k, v in value.items()}
        
        # List handling - process each item recursively
        elif isinstance(value, list):
            return [self._process_value_for_dict(item) for item in value]
        
        # Tuple handling - process each item recursively
        elif isinstance(value, tuple):
            return tuple(self._process_value_for_dict(item) for item in value)
            
        # Simple JSON serializable types
        elif isinstance(value, (str, int, float, bool, type(None))):
            return value
        
        # For any other types, convert to string
        else:
            return str(value)
    
    @classmethod
    def custom_json_encoder(cls, obj):
        """
        Custom JSON encoder for the configuration.
        """
        try:
            # Handle common built-in types first
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
                
            # Check for to_dict method
            if hasattr(obj, 'to_dict') and callable(obj.to_dict):
                return obj.to_dict()
                
            # Check if it's a Configurable object with a config attribute
            if hasattr(obj, 'config') and hasattr(obj.config, 'to_dict'):
                return obj.config.to_dict()
                
            # Try custom serialization for other types
            return str(obj)
        except (TypeError, ValueError):
            return repr(obj)

    def to_json_dict(self):
        """
        Serialize the configuration to JSON.
        """
        return json.dumps(self.to_dict(),
                          default=Config.custom_json_encoder, 
                          indent=4)

    def to_json(self, filename: str = None):
        with open(filename, 'w') as f:
            json.dump(self.to_dict(),
                      f,
                      default=Config.custom_json_encoder,
                      indent=4)
    
    def to_path_suffix(self):
        path_suffix = []
        for attr_name in self.__dict__.keys():
            attr_val = getattr(self, attr_name)
            if isinstance(attr_val, Config):
                path_suffix.append(attr_val.to_path_suffix())
            else:
                path_suffix.append(f'{attr_name}={attr_val}')

        return os.path.join(*path_suffix)

    def __hash__(self):
        return hash(self.to_json_dict())
    
    def to_sha256_str(self):
        hash_factory = hashlib.sha256()
        hash_factory.update(bytes(self.__str__(), 'ascii'))

        return hash_factory.hexdigest()
    
    def __str__(self):
        return self.to_json_dict()
    
    def __eq__(self, other):
        return self.to_sha256_str() == other.to_sha256_str()