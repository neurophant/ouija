import re
from typing import Optional


class RawParser:
    pattern = re.compile(
        br'(?P<method>[a-zA-Z]+) (?P<uri>(\w+://)?(?P<host>[^\s\'\"<>\[\]{}|/:]+)(:(?P<port>\d+))?[^\s\'\"<>\[\]{}|]*) ')
    uri: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    method: Optional[str] = None
    error: bool = False

    def __init__(self, *, data: bytes) -> None:
        rex = self.pattern.match(data)
        if rex:
            self.uri = self.to_str(item=rex.group('uri'))
            self.host = self.to_str(item=rex.group('host'))
            self.method = self.to_str(item=rex.group('method'))
            self.port = self.to_int(item=rex.group('port'))
        else:
            self.error = True

    @staticmethod
    def to_str(*, item: Optional[bytes]) -> Optional[str]:
        if item:
            return item.decode('charmap')

    @staticmethod
    def to_int(*, item: Optional[bytes]) -> Optional[int]:
        if item:
            return int(item)

    def __str__(self) -> str:
        return str(dict(URI=self.uri, HOST=self.host, PORT=self.port, METHOD=self.method))
