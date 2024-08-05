from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, TimeoutBehaviour, PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import time
import datetime
import json

DEFAULT_HOST = "server_hello"

class Predictor(Agent):
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        
    async def setup(self):
        print("Agent {} started".format(self.name))
        wfr = self.WaitForRequest()
        self.add_behaviour(wfr)

    class WaitForRequest(CyclicBehaviour):
        async def run(self):
            print("[{}]WaitForRequest beh running".format(self.agent.name))
            msg = await self.receive(timeout=1)  # wait for a message for 1 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
                pp = self.agent.ProvidePrediction(msg.get_metadata("sender"))
                self.agent.add_behaviour(pp)
    
    class ProvidePrediction(OneShotBehaviour):
        def __init__(self, sender: str):
            super().__init__(self)
            self.sender = sender

        async def run(self):
            print("[{}]ProvidePrediction beh running".format(self.agent.name))
           
            # Instantiate the message
            msg = Message(to=f"{self.agent.device_manager}@{DEFAULT_HOST}")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("sender", self.agent.name)
            msg.set_metadata("language", "json")

            await self.send(msg)
            print("SetWorkingPoint sent by {} to  {}".format(self.agent.name), self.agent.device_manager)
        