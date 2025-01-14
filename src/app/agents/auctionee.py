from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import json

from settings import (
    SERVER_HOST,
    AGENT_PASSWORD,
    VERIFY_SECURITY,
    BEHAVIOUR_TIMEOUT,
    DEBUG,
)


class Auctionee(Agent):

    def __init__(self, device_name: str, auction_operator_name: str):
        jid: str = f"{device_name}_auctionee@{SERVER_HOST}"
        password: str = AGENT_PASSWORD
        verify_security: bool = VERIFY_SECURITY
        super().__init__(jid, password, verify_security)

        self.device_name = device_name
        self.device_manager_name = f"{device_name}_manager"
        self.auction_operator_name = auction_operator_name

    async def setup(self):
        print(f"Auctionee Agent [{self.name}] started")
        wfm = self.WaitForMessage()
        self.add_behaviour(wfm)

    class WaitForMessage(CyclicBehaviour):

        _log_prefix_name = "WaitForMessage"

        async def run(self):
            agent: Auctionee = self.agent

            msg = await self.receive(timeout=BEHAVIOUR_TIMEOUT)
            if msg:
                if msg.get_metadata("performative") == "CFP":

                    msg_json = json.loads(msg.body)
                    timestamp = msg_json["timestamp"]

                    tojid = agent.device_manager_name
                    msg_rply = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg_rply.set_metadata("performative", "query")
                    msg_rply.set_metadata("sender", agent.name)
                    msg_rply.set_metadata("language", "json")
                    msg_rply.body = json.dumps({"timestamp": timestamp})

                    await self.send(msg_rply)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg_rply.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg_rply.body}]"
                        )

                if (
                    msg.get_metadata("performative") == "inform"
                    and msg.get_metadata("sender") == agent.device_manager_name
                ):
                    tojid = agent.auction_operator_name
                    msg_rply = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg_rply.set_metadata("performative", "propose")
                    msg_rply.set_metadata("language", "json")
                    msg_rply.body = msg.body

                    await self.send(msg_rply)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg_rply.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg_rply.body}]"
                        )

                if (
                    msg.get_metadata("performative") == "inform"
                    and msg.get_metadata("sender") == agent.auction_operator_name
                ):

                    tojid = agent.device_manager_name
                    msg_rply = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg_rply.set_metadata("performative", "accept_offer")
                    msg_rply.set_metadata("sender", agent.name)
                    msg_rply.set_metadata("language", "json")
                    msg_rply.body = msg.body

                    await self.send(msg_rply)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg_rply.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg_rply.body}]"
                        )
