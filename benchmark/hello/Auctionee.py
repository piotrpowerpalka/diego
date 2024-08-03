from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
from aioxmpp import JID as JID, PresenceShow, PresenceState
from asyncio import sleep
from datetime import datetime
from aioxmpp.structs import LanguageRange as LR

DEFAULT_HOST = "server_hello"

class Auctionee(Agent):

    async def setup(self):
        print("----- Auctionee Agent started")

        wfm = self.WaitForCFP()
        self.add_behaviour(wfm)
    
    class WaitForCFP(CyclicBehaviour):
        async def run(self):
            print("WaitForCFP beh running")
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")
                self.kill()

        async def on_end(self):
            await self.agent.stop()