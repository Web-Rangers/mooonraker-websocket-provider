from typing import NamedTuple, List

from src.abstract.models import JsonRpcResponse


class TemperatureDataValues(NamedTuple):
    temperatures: List[float]
    targets: List[float]
    powers: List[float]


class TemperatureResponse(NamedTuple):
    extruder: TemperatureDataValues
    heater_bed: TemperatureDataValues


def map_temperature_message(response: JsonRpcResponse) -> 'TemperatureResponse':
    result = response.result
    return TemperatureResponse(
        extruder=TemperatureDataValues(
            **result['extruder']
        ),
        heater_bed=TemperatureDataValues(
            **result['heater_bed']
        )
    )
