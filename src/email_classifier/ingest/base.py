from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ..models import Email


@runtime_checkable
class EmailSource(Protocol):
    def fetch(self) -> Iterable[Email]: ...
