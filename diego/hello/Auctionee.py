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
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.offer = {"volume": 10.0, "price": 25, "energy": 'active'}
        
    async def setup(self):
        print("{} Auctionee Agent started".format(self.name))

        wfm = self.WaitForCFP()
        self.add_behaviour(wfm)
    
    class WaitForCFP(CyclicBehaviour):
        async def run(self):
            print("[{}]WaitForCFP beh running".format(self.agent.name))
            msg = await self.receive(timeout=15*60)  # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
                # differentiate between active, and reactive energy

                so = self.agent.SendOffer()
                self.agent.add_behaviour(so)

                self.kill()
            else:
                print("Did not received any message after 10 seconds")
                self.kill()
    
    class SendOffer(OneShotBehaviour):
        async def run(self):
            print("[{}]SendOffer beh running".format(self.agent.name))
            
            # Instantiate the message
            msg = Message(to=f"auctionoperator@{DEFAULT_HOST}")
            msg.set_metadata("performative", "propose")
            msg.set_metadata("language", "json")
            msg.body = json.dumps(self.agent.offer)

            await self.send(msg)
            print("SendOffer sent by {} to  AuctionOperator".format(self.agent.name))

            wci = self.agent.WaitForClearingInfo()
            self.agent.add_behaviour(wci)

    class WaitForClearingInfo(CyclicBehaviour):
        async def run(self):
            print("WaitForClearingInfo beh running")
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))

                # ...

                self.kill()
            else:
                print("Did not received any message after 10 seconds")
                self.kill()

        async def on_end(self):
            wfm = self.agent.WaitForCFP()
            self.agent.add_behaviour(wfm)
            

    
