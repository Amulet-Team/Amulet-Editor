"""Final classes and methods at runtime.

This module provides a decorator interface to declare final
classes and methods.

This module is inspired by and is compatible with `typing.final`.
See PEP-591 (https://www.python.org/dev/peps/pep-0591) for more
details on this topic.

The main component of this module is the `final` decorator that
can be used to decorate classes and methods inside a class. As
such:

- Classes decorated with @final cannot be subclassed.
- Methods decorated with @final cannot be overriden in subclasses.

For more details, see: https://runtime-final.readthedocs.io

Copyright (C) I. Ahmad 2022-2023 - Licensed under MIT.

Refactored by gentlegiantJGC
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Set,
    Union,
    TypeVar,
)
import inspect

__all__ = (
    "final",
    "__author__",
    "__copyright__",
)

__author__ = "I. Ahmad (nerdguyahmad), gentlegiantJGC"
__copyright__ = "Copyright (C) I. Ahmad 2022-2023 - Licensed under MIT."

TargetType = Union[Callable[..., Any], type]
T = TypeVar("T", bound=TargetType)


@classmethod
def _forbid_subclassing(cls: Any) -> None:
    raise RuntimeError(f"Cannot subclass the final class {cls.__name__!r}")


def _forbid_methods(init_subclass):
    @classmethod
    def _forbid_overriding_finals(cls: Any) -> None:
        final_methods: Set[str] = getattr(cls, "__runtime_final_methods__", set())  # type: ignore
        overrides = vars(cls)

        for name in final_methods:
            if name in overrides:
                raise RuntimeError(
                    f"Cannot override {name!r} in class {cls.__name__!r}"
                )

        if init_subclass:
            init_subclass()

    return _forbid_overriding_finals


class _FinalFunction:
    """
    A class to ensure methods are not overridden.
    It stores the callable until it is set in a class at which point it patches the class.
    """

    def __init__(self, target: TargetType) -> None:
        self.target = target

    def __set_name__(self, owner: TargetType, name: str) -> None:
        name = self.target.__name__
        if not hasattr(owner, "__runtime_final_methods__"):
            owner.__runtime_final_methods__ = set()  # type: ignore
            owner.__init_subclass__ = _forbid_methods(owner.__init_subclass__)  # type: ignore
        owner.__runtime_final_methods__.add(name)  # type: ignore
        setattr(owner, name, self.target)

    def __call__(self, *args, **kwargs):
        raise RuntimeError(
            "The final decorator only works on methods assigned in a class."
        )


def _final(target: TargetType):
    """A decorator to indicate final methods and final classes.

    Use this decorator to indicate that the decorated method cannot be overridden, and decorated class cannot be subclassed.
    For example:

    >>> class Base:
    >>>     @final
    >>>     def done(self) -> None:
    >>>         ...
    >>> class Sub(Base):
    >>>     def done(self) -> None:  # RuntimeError raised
    >>>         ...
    >>>
    >>> @final
    >>> class Leaf:
    >>>     ...
    >>> class Other(Leaf):  # RuntimeError raised
    >>>     ...
    """
    target.__runtime_final__ = True  # type: ignore
    if inspect.isclass(target):
        target.__init_subclass__ = _forbid_subclassing  # type: ignore
        return target
    elif inspect.isfunction(target):
        return _FinalFunction(target)
    else:
        raise RuntimeError(
            "The final decorator can only be used with classes and methods."
        )


if TYPE_CHECKING:
    from typing import final
else:
    final = _final
