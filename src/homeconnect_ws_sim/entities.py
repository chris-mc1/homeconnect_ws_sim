from __future__ import annotations

import asyncio
from abc import ABC
from typing import TYPE_CHECKING, Any

from homeconnect_websocket.entities import Access
from homeconnect_websocket.helpers import TYPE_MAPPING
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from homeconnect_websocket.entities import EntityDescription

    from .appliance import SimAppliance


class Entity(ABC):
    """BaseEntity Class."""

    _appliance: SimAppliance
    _uid: int
    _name: str
    _callbacks: set[Callable[[Entity], Coroutine]]
    _tasks: set[asyncio.Task]
    _value: Any | None = None
    _enumeration: dict | None = None
    _rev_enumeration: dict
    _description_change: dict[str]

    def __init__(self, description: EntityDescription, appliance: SimAppliance) -> None:
        self._appliance = appliance
        self._description = description
        self._uid = description["uid"]
        self._name = description["name"]
        self._tasks = set()
        self._callbacks = set()
        self._description_change = {}
        self._protocol_type = description.get("protocolType")
        self._content_type = description.get("contentType")
        self._type = TYPE_MAPPING.get(description.get("protocolType"), lambda value: value)
        if "enumeration" in description:
            self._enumeration = {int(k): v for k, v in description["enumeration"].items()}
            self._rev_enumeration = {v: int(k) for k, v in description["enumeration"].items()}
        if "initValue" in description:
            self._value = self._type(description["initValue"])
        if "default" in description:
            self._value = self._type(description["default"])

    def dump(self) -> dict:
        """Dump Entity state."""
        return {
            "uid": self.uid,
            "name": self.name,
            "value": self.value,
            "value_raw": self.value_raw,
            "enum": self.enum,
            "protocolType": self._protocol_type,
            "contentType": self._content_type,
        }

    async def set_state(self, state: dict) -> None:
        if "value_raw" in state and state["value_raw"] is not None:
            await self.set_value_raw(state["value_raw"])
        if self._description_change:
            self._description_change["uid"] = self._uid
            message = Message(
                resource="/ro/descriptionChange",
                action=Action.NOTIFY,
                data=[self._description_change],
            )
            await self._appliance.send(message)
            self._description_change = {}

    def get_description_changes(self) -> dict:
        return {"uid": self._uid}

    async def update(self, values: dict) -> None:
        """Update the entity state and execute callbacks."""
        if "value" in values:
            self._value = self._type(values["value"])

            message = Message(
                resource="/ro/values",
                action=Action.NOTIFY,
                data={"uid": self._uid, "value": self._value},
            )
            await self._appliance.send(message)

        for callback in self._callbacks:
            task = asyncio.create_task(callback(self))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.remove)

    def register_callback(self, callback: Callable[[Entity], Coroutine]) -> None:
        """Register update callback."""
        if callback not in self._callbacks:
            self._callbacks.add(callback)

    def unregister_callback(self, callback: Callable[[Entity], Coroutine]) -> None:
        """Unregister update callback."""
        self._callbacks.remove(callback)

    @property
    def uid(self) -> int:
        """Entity uid."""
        return self._uid

    @property
    def name(self) -> str:
        """Entity name."""
        return self._name

    @property
    def value(self) -> Any | None:
        """
        Current Value of the Entity.

        if the Entity is an Enum entity the value will be resolve to the actual value.
        """
        if self._enumeration and self._value is not None:
            return self._enumeration[self._value]
        return self._value

    async def set_value(self, value: str | int | bool) -> None:
        """
        Set the Value of the Entity.

        if the Entity is an Enum entity the value will be resolve to the reference Value
        """
        if self._enumeration:
            if value not in self._rev_enumeration:
                msg = "Value not in Enum"
                raise ValueError(msg)
            await self.set_value_raw(self._rev_enumeration[value])
        else:
            await self.set_value_raw(value)

    @property
    def value_raw(self) -> Any | None:
        """Current raw Value."""
        return self._value

    async def set_value_raw(self, value_raw: str | float | bool) -> None:
        """Set the raw Value."""
        value_raw = self._type(value_raw)
        if self._value != value_raw:
            self._value = value_raw
            message = Message(
                resource="/ro/values",
                action=Action.NOTIFY,
                data={"uid": self._uid, "value": value_raw},
            )
            await self._appliance.send(message)

    @property
    def enum(self) -> dict[int, str] | None:
        """The internal enumeration."""
        return self._enumeration


class AccessMixin(Entity):
    """Mixin for Entities with access attribute."""

    _access: Access | None = None

    def __init__(self, description: EntityDescription, appliance: SimAppliance) -> None:
        """
        Mixin for Entities with access attribute.

        Args:
        ----
            description (EntityDescription): The entity description
            appliance (SimAppliance): Appliance

        """
        super().__init__(description, appliance)
        self._access = Access(description.get("access", self._access).lower())

    @property
    def access(self) -> Access | None:
        """Current Access state."""
        return self._access

    def dump(self) -> dict:
        """Dump Entity state."""
        state = super().dump()
        state["access"] = self._access.value.upper()
        return state

    def get_description_changes(self) -> dict:
        changes = super().get_description_changes()
        if self._access != self._description.get("access", None):
            changes["access"] = self._access.value.upper()
        return changes

    async def set_state(self, state: dict) -> None:
        if "access" in state and self._access != Access(state["access"].lower()):
            self._access = Access(state["access"].lower())
            self._description_change["access"] = self._access.value.upper()
        await super().set_state(state)


class AvailableMixin(Entity):
    """Mixin for Entities with available attribute."""

    _available: bool | None = None

    def __init__(self, description: EntityDescription, appliance: SimAppliance) -> None:
        """
        Mixin for Entities with available attribute.

        Args:
        ----
            description (EntityDescription): The entity description
            appliance (SimAppliance): Appliance

        """
        super().__init__(description, appliance)
        self._available = description.get("available", self._available)

    @property
    def available(self) -> bool | None:
        """Current Available state."""
        return self._available

    def dump(self) -> dict:
        """Dump Entity state."""
        state = super().dump()
        state["available"] = self.available
        return state

    def get_description_changes(self) -> dict:
        changes = super().get_description_changes()
        if self._available != self._description.get("available", None):
            changes["available"] = self._available
        return changes

    async def set_state(self, state: dict) -> None:
        if "available" in state and self._available != state["available"]:
            self._available = state["available"]
            self._description_change["available"] = self._available
        await super().set_state(state)


class MinMaxMixin(Entity):
    """Mixin for Entities with available Min and Max values."""

    _min: float | None = None
    _max: float | None = None
    _step: float | None = None

    def __init__(self, description: EntityDescription, appliance: SimAppliance) -> None:
        """
        Mixin for Entities with available Min and Max values.

        Args:
        ----
            description (EntityDescription): The entity description
            appliance (SimAppliance): Appliance

        """
        self._min_max_type = TYPE_MAPPING.get(description.get("protocolType"), lambda value: value)
        super().__init__(description, appliance)
        if "min" in description:
            self._min = self._min_max_type(description["min"])
        if "max" in description:
            self._max = self._min_max_type(description["max"])
        if "stepSize" in description:
            self._step = self._min_max_type(description["stepSize"])

    @property
    def min(self) -> float | None:
        """Minimum value."""
        return self._min

    @property
    def max(self) -> float | None:
        """Maximum value."""
        return self._max

    @property
    def step(self) -> float | None:
        """Minimum value."""
        return self._step

    def dump(self) -> dict:
        """Dump Entity state."""
        state = super().dump()
        state["min"] = self.min
        state["max"] = self.max
        state["step"] = self.step
        return state

    def get_description_changes(self) -> dict:
        changes = super().get_description_changes()

        if (
            "min" in self._description and self._min != self._min_max_type(self._description["min"])
        ) or ("min" not in self._description and self._min is not None):
            changes["min"] = self._min_max_type(self._min)

        if (
            "max" in self._description and self._max != self._min_max_type(self._description["max"])
        ) or ("max" not in self._description and self._max is not None):
            changes["max"] = self._min_max_type(self._max)

        if (
            "stepSize" in self._description
            and self._step != self._min_max_type(self._description["stepSize"])
        ) or ("stepSize" not in self._description and self._step is not None):
            changes["step"] = self._min_max_type(self._step)

        return changes

    async def set_state(self, state: dict) -> None:
        if "min" in state and self._min != state["min"]:
            self._min = self._min_max_type(state["min"])
            self._description_change["min"] = self._min
        if "max" in state and self._max != state["max"]:
            self._max = self._min_max_type(state["max"])
            self._description_change["max"] = self._max
        if "stepSize" in state and self._step != state["stepSize"]:
            self._step = self._min_max_type(state["stepSize"])
            self._description_change["stepSize"] = self._step
        await super().set_state(state)


class Status(AccessMixin, AvailableMixin, MinMaxMixin, Entity):
    """Represents an Settings Entity."""


class Setting(AccessMixin, AvailableMixin, MinMaxMixin, Entity):
    """Represents an Settings Entity."""


class Event(Entity):
    """Represents an Event Entity."""

    _value = 0


class Command(AccessMixin, AvailableMixin, MinMaxMixin, Entity):
    """Represents an Command Entity."""


class Option(AccessMixin, AvailableMixin, MinMaxMixin, Entity):
    """Represents an Option Entity."""


class Program(AvailableMixin, Entity):
    """Represents an Program Entity."""


class ActiveProgram(AccessMixin, AvailableMixin, Entity):
    """Represents the Active_Program Entity."""

    _available = True


class SelectedProgram(AccessMixin, AvailableMixin, Entity):
    """Represents the Selected_Program Entity."""

    _available = True


class ProtectionPort(AccessMixin, AvailableMixin, Entity):
    """Represents an Protection_Port Entity."""

    _available = False
