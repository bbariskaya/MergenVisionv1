from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NationalIdProtectedValue:
    ciphertext: bytes
    lookup_hash: str
    masked: str

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"ciphertext=<{len(self.ciphertext)} bytes>, "
            f"lookup_hash=<{len(self.lookup_hash)} chars>, "
            f"masked={self.masked!r})"
        )


class NationalIdProtector(ABC):
    @abstractmethod
    def protect(self, raw_national_id: str) -> NationalIdProtectedValue:
        raise NotImplementedError

    @abstractmethod
    def reveal(self, protected: NationalIdProtectedValue) -> str:
        raise NotImplementedError
