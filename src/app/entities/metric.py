from dataclasses import dataclass


@dataclass(slots=True)
class Metric:

    device_name: str
    timestamp: str
    active_power: float
    reactive_power: float
    active_energy: float
    reactive_energy: float

    def to_spade_message(self) -> dict:
        """

        Returns:
        {
        "Datetime": "2024-01-31 00:30:00",
        "bystar1_P": "9.84638707",
        "bystar1_Q": "-6.268445866",
        "bystar1_Ep": "2.462016229",
        "bystar1_Eq": "-1.59490697"
        }

        """
        return {
            "Datetime": self.timestamp,
            f"{self.device_name}_P": self.active_power,
            f"{self.device_name}_Q": self.reactive_power,
            f"{self.device_name}_Ep": self.active_energy,
            f"{self.device_name}_Eq": self.reactive_energy,
        }
