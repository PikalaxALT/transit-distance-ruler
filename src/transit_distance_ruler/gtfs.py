import partridge
from pandas import DataFrame
from sqlalchemy.ext.declarative import declarative_base


class TransitDB:
    def __init__(self):
        self.all_agencies = []

    def load(self):
        return NotImplemented

    def get_supported_modes(self, agency: str) -> list[str]:
        return NotImplemented

    def get_routes(self, agency: str, mode: str) -> list[str]:
        return NotImplemented

    def get_route_directions(self, agency: str, mode: str, route: str) -> list[str]:
        return NotImplemented

    def get_stops(
        self, agency: str, mode: str, route: str, direction: bool
    ) -> list[str]:
        return NotImplemented

    def get_route_frame(
        self, agency: str, mode: str, route: str, direction: bool, start: str, end: str
    ) -> DataFrame:
        return NotImplemented
