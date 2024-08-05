from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, TimeoutBehaviour, PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import time
import datetime
import json

DEFAULT_HOST = "server_hello"

class DeviceManager(Agent):
    def __init__(self, jid: str, password: str, config: dict, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.config = config
        
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
                # predict something smart...



                
        