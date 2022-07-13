"""
Python Module for Pydantic Models and validation
"""
import functools
import importlib
import warnings
from inspect import signature
from types import ModuleType
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Union

from pydantic import EmailStr, Extra, root_validator, validator
from pydantic_yaml import YamlModel


class Action(YamlModel):
    """
    Action is the inner model for each action in the configuration file"""

    action_tag: str
    module: str = "src.jbi.whiteboard_actions.default"
    # TODO: Remove the tbd literal option when all actions have contact info # pylint: disable=fixme
    contact: Union[EmailStr, List[EmailStr], Literal["tbd"]]
    description: str
    enabled: bool = False
    allow_private: bool = False
    parameters: dict = {}

    @functools.cached_property
    def callable(self) -> Callable:
        """Return the initialized callable for this action."""
        action_module: ModuleType = importlib.import_module(self.module)
        initialized: Callable = action_module.init(**self.parameters)  # type: ignore
        return initialized

    @root_validator
    def validate_action_config(cls, values):  # pylint: disable=no-self-argument
        """Validate action: exists, has init function, and has expected params"""
        try:
            module: str = values["module"]  # type: ignore
            action_parameters: Optional[Dict[str, Any]] = values["parameters"]
            action_module: ModuleType = importlib.import_module(module)
            if not action_module:
                raise TypeError("Module is not found.")
            if not hasattr(action_module, "init"):
                raise TypeError("Module is missing `init` method.")

            signature(action_module.init).bind(**action_parameters)  # type: ignore
        except ImportError as exception:
            raise ValueError(f"unknown Python module `{module}`.") from exception
        except (TypeError, AttributeError) as exception:
            raise ValueError(f"action is not properly setup.{exception}") from exception
        return values

    class Config:
        """Pydantic configuration"""

        extra = Extra.allow
        keep_untouched = (functools.cached_property,)


class Actions(YamlModel):
    """
    Actions is the container model for the list of actions in the configuration file
    """

    __root__: List[Action]

    @functools.cached_property
    def by_tag(self) -> Mapping[str, Action]:
        """Build mapping of actions by lookup tag."""
        return {a.action_tag: a for a in self.__root__}

    def __len__(self):
        return len(self.__root__)

    def __getitem__(self, item):
        return self.by_tag[item]

    def get(self, tag: Optional[str]) -> Optional[Action]:
        """Lookup actions by whiteboard tag"""
        return self.by_tag.get(tag.lower()) if tag else None

    @validator("__root__")
    def validate_actions(  # pylint: disable=no-self-argument
        cls, actions: List[Action]
    ):
        """
        Inspect the list of actions:
         - There is at least one action
         - Validate that lookup tags are uniques
         - If the action's contact is "tbd", emit a warning.
        """
        if not actions:
            raise ValueError("no actions configured")

        tags = [a.action_tag.lower() for a in actions]
        duplicated_tags = [t for i, t in enumerate(tags) if t in tags[:i]]
        if duplicated_tags:
            raise ValueError(f"actions have duplicated lookup tags: {duplicated_tags}")

        for action in actions:
            if action.contact == "tbd":
                warnings.warn(f"Provide contact data for `{action.action_tag}` action.")

        return actions

    class Config:
        """Pydantic configuration"""

        keep_untouched = (functools.cached_property,)
