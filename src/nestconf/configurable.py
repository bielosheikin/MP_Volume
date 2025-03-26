from dataclasses import make_dataclass, field, Field
from abc import ABCMeta
import sys
from .config import Config
import pickle

# Dictionary to store dynamically created Config classes
CONFIG_CLASSES = {}

class ConfigurableMeta(type):
    def __new__(cls, name, bases, dct): 
        # Create the Configurable class
        configurable_cls = super().__new__(cls, name, bases, dct)

        config_fields = []
        if '__annotations__' in dct:
            for field_name, field_type in dct['__annotations__'].items():
                if isinstance(dct[field_name], Field):
                    config_fields.append((field_name, 
                                        field_type,
                                        dct[field_name]))
                else:
                    config_fields.append((field_name,
                                        field_type,
                                        field(default=dct[field_name])))
                    
            # Define the dynamically created Config class
            config_name = f"{name}Config"
            config_class = make_dataclass(
                config_name,  # Name of the dynamically created class
                fields=config_fields,  # Dynamically extracted fields
                bases=(Config,),  # Inherit from the base Config class
            )
            
            # Store the config class in our global registry
            CONFIG_CLASSES[config_name] = config_class
            
            # Register the config class in the module for pickling
            module = sys.modules[configurable_cls.__module__]
            setattr(module, config_name, config_class)
            
            # Attach the dynamically created Config class to the Configurable
            setattr(configurable_cls, "BOUND_CONFIG_CLASS", config_class)
            setattr(configurable_cls, "CONFIG_CLASS_NAME", config_name)

            for field_name, _, _ in config_fields:
                def make_property(field_name):
                    # Define a property dynamically with both getter and setter
                    def getter(self):
                        return getattr(self.config, field_name)
                    def setter(self, value):
                        setattr(self.config, field_name, value)
                    return property(getter, setter)
                setattr(configurable_cls, field_name, make_property(field_name))

        return configurable_cls


class CombinedMeta(ConfigurableMeta, ABCMeta):
    """A metaclass that combines ConfigurableMeta and ABCMeta."""
    pass


class Configurable(metaclass=CombinedMeta):
    def __init__(self, 
                 *,
                 config: Config = None,
                 **kwargs):
        # Use the dynamically created Config class
        if config is None:
            self.config = self.BOUND_CONFIG_CLASS()
        else:
            if not isinstance(config, self.BOUND_CONFIG_CLASS):
                raise TypeError(f"Expected {self.BOUND_CONFIG_CLASS}, got {type(config)}.")
            else:
                self.config = config
        for arg_name, arg_val in kwargs.items():
            if hasattr(self.config, arg_name):
                setattr(self.config, arg_name, arg_val)
    
    def __reduce__(self):
        """
        Support for pickling by capturing the state needed to reconstruct the object.
        Return a callable object that will recreate this object and the args to pass to it.
        """
        class_name = self.__class__.__name__
        config_dict = {k: getattr(self.config, k) for k in self.config.__dict__ if not k.startswith('_')}
        state = {'config_dict': config_dict}
        
        # Add any instance attributes that aren't in the config
        for attr in self.__dict__:
            if attr != 'config':
                state[attr] = getattr(self, attr)
        
        return (Configurable._reconstructor, (class_name, state))
    
    @staticmethod
    def _reconstructor(class_name, state):
        """
        Helper function to reconstruct a Configurable object during unpickling.
        """
        # Find the class in the module
        for module_name, module in sys.modules.items():
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                if issubclass(cls, Configurable):
                    # Create a new instance with the config values
                    config_dict = state.pop('config_dict')
                    instance = cls(**config_dict)
                    
                    # Restore any other instance attributes
                    for attr, value in state.items():
                        setattr(instance, attr, value)
                    
                    return instance
        
        raise ValueError(f"Could not find class {class_name} in any module")