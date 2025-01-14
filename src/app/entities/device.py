from dataclasses import dataclass, field


@dataclass(slots=True)
class Bounds:
    """
    Bounds class is responsible for defining the bounds of a device.

    Example from csv:
    ;min;max
    pv_P;-317.12;0.2
    pv_tg;0;0.75
    eh_P;0;4
    eh_Q;0;0
    evcs_P;0;10.5
    evcs_Q;-1.2;0.05
    inv1_P;-50;50
    inv1_tg;circ;circ

    """

    attribute: str
    min: float | str
    max: float | str


@dataclass(slots=True)
class Roles:
    """
    Roles class is responsible for defining the roles of a device.

    Example from csv:
    flow;role;energy;price;device
    pv_Ep;UAS;Ep;1;pv
    pv_Eq;CA;Eq;1;pv
    eh_Ep;CA;Ep;4;eh
    eh_Eq;UA;Eq;1;eh
    evcs_Ep;CA;Ep;4;evcs
    evcs_Eq;UA;Eq;6;evcs
    inv1_Ep;CA;Ep;2;inv1
    inv1_Eq;CA;Eq;5;inv1
    inv2_Ep;NCA;Ep;2;inv2
    inv2_Eq;NCA;Eq;5;inv2
    bystar1_Ep;UA;Ep;8;bystar1
    bystar1_Eq;UA;Eq;8;bystar1
    bysprint_Ep;UA;Ep;8;bysprint
    bysprint_Eq;UA;Eq;8;bysprint
    bystar2_Ep;UA;Ep;8;bystar2
    bystar2_Eq;UA;Eq;8;bystar2
    mazak_Ep;UA;Ep;8;mazak
    mazak_Eq;UA;Eq;8;mazak
    network;CA;Ep;10;network
    network;CA;Eq;10;network


    """

    role_type: str
    energy_type: str
    price: float


@dataclass(slots=True)
class DeviceProperties:

    device_name: str
    bounds_list: list[Bounds] = field(init=False)
    roles_list: list[Roles] = field(init=False)

    @staticmethod
    def from_json(properties_json: dict) -> "DeviceProperties":

        device_name = properties_json["deviceName"]
        properties = DeviceProperties(device_name=device_name)
        properties._parse(properties_json)
        return properties

    def _parse(self, properties_json: dict):
        """
        Parse the properties JSON.

        Args:
        {
        "deviceName": "pv",
        "bounds": [
          {
            "attribute": "P",
            "min": -317.12,
            "max": 0.2
          },
          {
            "attribute": "tg",
            "min": 0,
            "max": 0.75
          }
        ],
        "roles": [
          {
            "roleType": "UAS",
            "energyType": "Ep",
            "price": 1
          },
          {
            "roleType": "CA",
            "energyType": "Eq",
            "price": 1
          }
        ]
        }
        """
        bounds_list = []
        bounds = properties_json["bounds"]
        if bounds is not None:
            for bound in bounds:
                bounds_list.append(Bounds(**bound))
        self.bounds_list = bounds_list

        roles_list = []
        roles = properties_json["roles"]
        if roles is not None:
            for role in roles:
                roles_list.append(
                    Roles(
                        role_type=role["roleType"],
                        energy_type=role["energyType"],
                        price=role["price"],
                    )
                )
        self.roles_list = roles_list

    def roles_to_spade_message(self) -> dict:
        """
        Returns:
        {
          "flow": ["bystar1_Ep", "bystar1_Eq"],
          "role": ["UA", "UA"],
          "energy": ["Ep", "Eq"],
          "price": ["8.0", "8.0"],
          "device": ["bystar1", "bystar1"]
        }
        """
        message = {
            "flow": [],
            "role": [],
            "energy": [],
            "price": [],
            "device": [],
        }
        for role in self.roles_list:
            message["flow"].append(f"{self.device_name}_{role.energy_type}")
            message["role"].append(role.role_type)
            message["energy"].append(role.energy_type)
            message["price"].append(str(role.price))
            message["device"].append(self.device_name)

        return message

    def bounds_to_spade_message(self) -> dict:
        """
        Returns:
        {
          "Unnamed: 0": ["bystar1_P", "bystar1_Q"],
          "min": ["0.0", "-15.0"],
          "max": ["33.0", "10.0"]
        }
        """
        message = {
            "Unnamed: 0": [],
            "min": [],
            "max": [],
        }
        for bound in self.bounds_list:
            message["Unnamed: 0"].append(f"{self.device_name}_{bound.attribute}")
            message["min"].append(str(bound.min if bound.min is not None else "circ"))
            message["max"].append(str(bound.max if bound.max is not None else "circ"))

        return message
