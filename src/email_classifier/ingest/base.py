from typing import Iterable, Protocol, runtime_checkable

from ..models import Email


@runtime_checkable
class EmailSource(Protocol):
    def fetch(self) -> Iterable[Email]: ...
