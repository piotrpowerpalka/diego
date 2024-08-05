from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from aioxmpp import JID as JID, PresenceShow, PresenceState
from asyncio import sleep
from datetime import datetime
from aioxmpp.structs import LanguageRange as LR
import json

DEFAULT_HOST = "server_hello"

class Auctionee(Agent):
    def __init__(self, jid: str, password: str, config: dict, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.offer = {"volume": 10.0, "price": 25, "energy": 'active'}
        self.config = config
        self.energy_type = 0
        self.device_manager = self.config["device_manager"]
        
    async def setup(self):
        print("{} Auctionee Agent started".format(self.name))

        wfm = self.WaitForMessage()
        self.add_behaviour(wfm)
    
    class WaitForMessage(CyclicBehaviour):
        async def run(self):
            # print("[{}] WaitForCFP | WaitForClearningInfo | WaitForWorkingPoint|Bounds beh running".format(self.agent.name))
            msg = await self.receive(timeout=1)  # wait for a message forever
            if msg:
                if (msg.get_metadata("performative") == 'CFP' and msg.get_metadata("sender") == 'auctionoperator'):
                    # WaitForCFP...
                    msg_json = json.loads(msg.body)
                    energy_type = msg_json['energy']

                    ctrl = self.agent.config[energy_type]
                    if (ctrl == "controllable"):
                        self.energy_type = energy_type
                        gwpb = self.agent.GetWorkingPointBounds()
                        self.agent.add_behaviour(gwpb)

                    if (ctrl == "not_controllable"):
                        self.energy_type = energy_type
                        gwpi = self.agent.GetWorkingPointInfo()
                        self.agent.add_behaviour(gwpi)

                if (msg.get_metadata("performative") == 'inform' and msg.get_metadata("sender") == self.agent.device_manager):
                    # 
 #                   print("[{}] Message with Working point / bounds received: [{}]".format(self.agent.name, msg.body))

                    so = self.agent.SendOffer()
                    self.agent.add_behaviour(so)

                if (msg.get_metadata("performative") == 'inform' and msg.get_metadata("sender") == 'auctionoperator'):
                    # WaitForClearingInfo...
#                    print("[{}] Message with Clearing Info received: [{}]".format(self.agent.name, msg.body))

                    swp = self.agent.SetWorkingPoint()       
                    self.agent.add_behaviour(swp)            
                # 

                
    
    class SendOffer(OneShotBehaviour):
        async def run(self):
            print("[{}]SendOffer beh running".format(self.agent.name))
            
            # Instantiate the message
            tojid = f"auctionoperator@{DEFAULT_HOST}"
            msg = Message(to=tojid)
            msg.set_metadata("performative", "propose")
            msg.set_metadata("language", "json")
            msg.body = json.dumps(self.agent.offer)

            await self.send(msg)
            print("[{}][{}][{}]".format(self.agent.name, tojid, self.__class__.__name__))
            
            wci = self.agent.WaitForClearingInfo()
            self.agent.add_behaviour(wci)

    class SetWorkingPoint(OneShotBehaviour):
        async def run(self):
            print("[{}]SetWorkingPoint beh running".format(self.agent.name))
           
            # Instantiate the message
            tojid = self.agent.device_manager
            msg = Message(to=f"{tojid}@{DEFAULT_HOST}")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("sender", self.agent.name)
            msg.set_metadata("language", "json")

            await self.send(msg)
            print("[{}][{}][{}]".format(self.agent.name, tojid, self.__class__.__name__))
            

    class GetWorkingPointInfo(OneShotBehaviour):
        async def run(self):
            print("[{}]GetWorkingPointInfo beh running".format(self.agent.name))
           
            # Instantiate the message
            msg = Message(to=f"{self.agent.device_manager}@{DEFAULT_HOST}")
            msg.set_metadata("performative", "query")
            msg.set_metadata("sender", self.agent.name)
            msg.set_metadata("language", "json")
            msg.body = json.dumps({"energy": self.agent.energy_type})

            await self.send(msg)
            print("GetWorkingPointInfo sent by {} to  {}".format(self.agent.name, self.agent.device_manager))


    class GetWorkingPointBounds(OneShotBehaviour):
        async def run(self):
            print("[{}]GetWorkingPointBounds beh running".format(self.agent.name))
           
            # Instantiate the message
            msg = Message(to=f"{self.agent.device_manager}@{DEFAULT_HOST}")
            msg.set_metadata("performative", "query")
            msg.set_metadata("sender", self.agent.name)
            msg.set_metadata("language", "json")
            msg.body = json.dumps({"energy": self.agent.energy_type})

            await self.send(msg)
            print("GetWorkingPointBounds sent by {} to  {}".format(self.agent.name, self.agent.device_manager))
