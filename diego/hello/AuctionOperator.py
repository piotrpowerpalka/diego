from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, TimeoutBehaviour, PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import time
import datetime
import json

DEFAULT_HOST = "server_hello"

class AuctionOperator(Agent):
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.offers_list = []
        #self.auctionee_list = self.config['auctionees']
        self.auctionee_list = ['pv_auctionee', 'bystar_auctionee', 'byprint_auctionee']

    async def setup(self):
        print("Agent {} started".format(self.name))

        start_at1 = datetime.datetime.now()
        cfp = self.CallForProposal(period=60, start_at=start_at1)
        self.add_behaviour(cfp)

    class CallForProposal(PeriodicBehaviour):
        async def run(self):
#            print("[{}] CallForProposal beh running".format(self.agent.name))
            
            # behaviour ReceiveOffers added before sending offers, to avoid missing offers
            ro = self.agent.ReceiveOffers()
            self.agent.add_behaviour(ro)

            for curr_agent in self.agent.auctionee_list:

                tojid = f"{curr_agent}@{DEFAULT_HOST}"
                # Instantiate the message
                msg = Message(to=tojid)
                msg.set_metadata("performative", "CFP")
                msg.set_metadata("language", "json")
                msg.set_metadata("sender", self.agent.name)
                msg.body = json.dumps({"timestamp": "tu timestamp", "energy": "active"})

                await self.send(msg)
                print("[{}][{}][{}]".format(self.agent.name, tojid, self.__class__.__name__))
    
    class ReceiveOffers(CyclicBehaviour):
        async def run(self):
            # print("[{}] ReceiveOffers beh running".format(self.agent.name))
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
#                print("[{}] Message received with content: {}".format(self.agent.jid, msg.body))
                if (msg.get_metadata("language") == "json"):
                    self.agent.offers_list.append(json.loads(msg.body))
                else:
                    raise TypeError 

                if (len(self.agent.offers_list) == len(self.agent.auctionee_list)):
                    self.kill()

            else:
                print("[{}] ReceiveOffers: did not received any message after 10 seconds".format(self.agent.name))
                self.kill()
            
        async def on_end(self):
            cl = self.agent.Clear()
            self.agent.add_behaviour(cl)


    class Clear(OneShotBehaviour):
        async def run(self):
            print("[{}]Clear beh running".format(self.agent.name))
            # insert code for clearing the offers

            sci = self.agent.SendClearingInfo()
            self.agent.add_behaviour(sci)

    
    class SendClearingInfo(OneShotBehaviour):
        async def run(self):
            print("[{}] SendClearingInfo beh running".format(self.agent.jid))
            for curr_agent in self.agent.auctionee_list:

                tojid = f"{curr_agent}@{DEFAULT_HOST}"
                # Instantiate the message
                msg = Message(to=tojid)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("sender", self.agent.name)
                msg.body = "Siema byku !"

                await self.send(msg)
                print("[{}][{}][{}]".format(self.agent.name, tojid, self.__class__.__name__))




            

