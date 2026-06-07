from __future__ import annotations


class StringPool:
    def __init__(self) -> None:
        self._strings: list[str] = [""]
        self._index: dict[str, int] = {"": 0}

    def add(self, s: str) -> int:
        if s in self._index:
            return self._index[s]
        idx = len(self._strings)
        self._strings.append(s)
        self._index[s] = idx
        return idx

    def get(self, idx: int) -> str:
        return self._strings[idx]

    @property
    def count(self) -> int:
        return len(self._strings)

    def encode(self) -> bytes:
        return b"".join(s.encode("utf-8") + b"\x00" for s in self._strings)

    @classmethod
    def decode(cls, data: bytes, count: int) -> StringPool:
        pool = cls()
        pool._strings = []
        pool._index = {}
        offset = 0
        for i in range(count):
            end = data.index(0, offset)
            s = data[offset:end].decode("utf-8")
            pool._strings.append(s)
            pool._index[s] = i
            offset = end + 1
        return pool
