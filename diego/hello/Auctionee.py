from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from aioxmpp import JID as JID, PresenceShow, PresenceState
from asyncio import sleep
from datetime import datetime
from aioxmpp.structs import LanguageRange as LR
import json
from functions import *
from json import dumps
from pandas import Timedelta

DEFAULT_HOST = "server_hello"

class Auctionee(Agent):
    def __init__(self, jid: str, password: str, config: dict, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.offer = {"volume": 10.0, "price": 25, "energy": 'active'}
        self.config = config
        self.device_manager = self.config["device_manager"]
        self.auction_operator = self.config["auction_operator"]
        
    async def setup(self):
        print("{} Auctionee Agent started".format(self.name))

        wfm = self.WaitForMessage()
        self.add_behaviour(wfm)
    
    class WaitForMessage(CyclicBehaviour):
        async def run(self):
            # print("[{}] WaitForCFP | WaitForClearningInfo | WaitForWorkingPoint|Bounds beh running".format(self.agent.name))
            msg = await self.receive(timeout=120)  # wait for a message forever
            if msg:
                if (msg.get_metadata("performative") == 'CFP'):
                    # WaitForCFP...
                    msg_json = json.loads(msg.body)
                    timestamp = msg_json["timestamp"]
                    # ctrl = self.agent.config[energy_type]
                    ctrl = self.agent.config["active"]

                    if (ctrl == "controllable"):
                        # [GetWorkingPointBounds] - from Auctionee - send it to DeviceManager
                        # self.energy_type = energy_type
                        tojid=self.agent.device_manager
                        msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                        msg_rply.set_metadata("performative", "query")
                        msg_rply.set_metadata("sender", self.agent.name)
                        msg_rply.set_metadata("language", "json")
                        # msg_rply.body = json.dumps({"type": "working_point_bounds", "energy": msg_json['energy'], "timestamp": timestamp})
                        msg_rply.body = json.dumps({"type": "working_point_bounds", "timestamp": timestamp})


                        await self.send(msg_rply)
                        print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: DeviceManager".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

                    if (ctrl == "not_controllable"):
                        # [GetWorkingPointInfo] - from Auctionee - send it to DeviceManager
                        # self.energy_type = energy_type
                        tojid=self.agent.device_manager
                        msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                        msg_rply.set_metadata("performative", "query")
                        msg_rply.set_metadata("sender", self.agent.name)
                        msg_rply.set_metadata("language", "json")
                        #msg_rply.body = json.dumps({"type": "working_point_info", "energy": msg_json['energy'], "timestamp": timestamp})
                        msg_rply.body = json.dumps({"type": "working_point_info", "timestamp": timestamp})

                        await self.send(msg_rply)
                        print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: DeviceManager".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

                if (msg.get_metadata("performative") == 'inform' and msg.get_metadata("sender") == self.agent.device_manager):
                    tojid = self.agent.auction_operator
                    msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                    msg_rply.set_metadata("performative", "propose")
                    msg_rply.set_metadata("language", "json")
                    msg_rply.body = msg.body
                
                    await self.send(msg_rply)
                    print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: AucitonOperator".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

                if (msg.get_metadata("performative") == 'inform' and msg.get_metadata("sender") == self.agent.auction_operator):
                    # WaitForClearingInfo...
#                    print("[{}] Message with Clearing Info received: [{}]".format(self.agent.name, msg.body))

                     # Instantiate the message
                    tojid = self.agent.device_manager
                    msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                    msg_rply.set_metadata("performative", "accept_offer")
                    msg_rply.set_metadata("sender", self.agent.name)
                    msg_rply.set_metadata("language", "json")  
                    msg_rply.body = msg.body

                    await self.send(msg_rply)
                    print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Device Manager".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))
                

                
    
            
