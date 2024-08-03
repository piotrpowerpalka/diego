from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, TimeoutBehaviour, PeriodicBehaviour
from spade.message import Message
from spade.template import Template
import time
import datetime

DEFAULT_HOST = "server_hello"

class AuctionOperator(Agent):
    async def setup(self):
        print("----- AuctionOperator Agent started")

        start_at1 = datetime.datetime.now() + datetime.timedelta(seconds=5)
        cfp = self.CallForProposal(period=5, start_at=start_at1)
        self.add_behaviour(cfp)

    class CallForProposal(PeriodicBehaviour):
        async def run(self):
            print("CallForProposal beh running")
            agent_list_test = ['pv_auctionee']

            print("---> Call for proposal by AuctionOperator running")

            for curr_agent in agent_list_test:

                to_jid = f"{curr_agent}@{DEFAULT_HOST}"

                # Instantiate the message
                msg = Message(to=to_jid)
                msg.set_metadata("performative", "CFP")
                msg.body = "..."

                print("-------> CFP prepared to sent by AuctionOperator to: [{}]\n". format(curr_agent))
                await self.send(msg)
                print("-------> CFP sent by AuctionOperator to: [{}]\n". format(curr_agent))

