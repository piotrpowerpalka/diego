import spade
import sys
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
from DeviceManager import *
from AuctionOperator import *
from Auctionee import *
from Predictor import *
import time
import csv
import datetime
import os
import asyncio

DEFAULT_HOST = "server_hello"
AGENT_PASSWORD = "123456789"


async def main():
    # uruchamiamy tyle agentów DeviceManager ile urządzeń, wiążemy je (nazwą) z agentami Auctoinee
    prd_pv       = Predictor(f"pv_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "pv", verify_security=False)
    prd_bystar1  = Predictor(f"bystar1_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "bystar1", verify_security=False)
    prd_bystar2  = Predictor(f"bystar2_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "bystar2", verify_security=False)
    prd_mazak    = Predictor(f"mazak_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "mazak", verify_security=False)
    prd_eh       = Predictor(f"eh_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "eh", verify_security=False)
    prd_inv1     = Predictor(f"inv1_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "inv1", verify_security=False)
    prd_inv2     = Predictor(f"inv2_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "inv1", verify_security=False)
    prd_sg1     = Predictor(f"sg1_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg1", verify_security=False)
    prd_sg2     = Predictor(f"sg2_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg2", verify_security=False)
    prd_sg3     = Predictor(f"sg3_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg3", verify_security=False)
    prd_sg4     = Predictor(f"sg4_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg4", verify_security=False)
    
    # uruchamiamy tyle agentów DeviceManager ile urządzeń, wiążemy je (nazwą) z agentami Auctoinee
    dm_pv       = DeviceManager(f"pv_device@{DEFAULT_HOST}",        AGENT_PASSWORD, "pv", {"predictor": "pv_predictor", "auctionee": "pv_auctionee"}, verify_security=False)
    dm_bystar1  = DeviceManager(f"bystar1_device@{DEFAULT_HOST}",  AGENT_PASSWORD, "bystar1", {"predictor": "bystar1_predictor", "auctionee": "bystar1_auctionee"}, verify_security=False)
    dm_bystar2  = DeviceManager(f"bystar2_device@{DEFAULT_HOST}",  AGENT_PASSWORD, "bystar2", {"predictor": "bystar2_predictor", "auctionee": "bystar2_auctionee"}, verify_security=False)
    dm_mazak    = DeviceManager(f"mazak_device@{DEFAULT_HOST}",    AGENT_PASSWORD, "mazak", {"predictor": "mazak_predictor", "auctionee": "mazak_auctionee"}, verify_security=False)
    dm_eh       = DeviceManager(f"eh_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "eh", {"predictor": "eh_predictor", "auctionee": "eh_auctionee"}, verify_security=False)
    dm_inv1     = DeviceManager(f"inv1_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "inv1", {"predictor": "inv1_predictor", "auctionee": "inv1_auctionee"}, verify_security=False)
    dm_inv2     = DeviceManager(f"inv2_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "inv2", {"predictor": "inv2_predictor", "auctionee": "inv2_auctionee"}, verify_security=False)
    dm_sg1     = DeviceManager(f"sg1_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "sg1", {"predictor": "sg1_predictor", "auctionee": "sg1_auctionee"}, verify_security=False)
    dm_sg2     = DeviceManager(f"sg2_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "sg2", {"predictor": "sg2_predictor", "auctionee": "sg2_auctionee"}, verify_security=False)
    dm_sg3     = DeviceManager(f"sg3_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "sg3", {"predictor": "sg3_predictor", "auctionee": "sg3_auctionee"}, verify_security=False)
    dm_sg4     = DeviceManager(f"sg4_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "sg4", {"predictor": "sg4_predictor", "auctionee": "sg4_auctionee"}, verify_security=False)
    
    # uruchamiamy tyle agentów Auctionee ile urządzeń
    auc_pv = Auctionee(f"pv_auctionee@{DEFAULT_HOST}",             AGENT_PASSWORD, {"active": "not_controllable", "reactive": "controllable", "device_manager": "pv_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_bystar1 = Auctionee(f"bystar1_auctionee@{DEFAULT_HOST}",   AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "bystar1_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_bystar2 = Auctionee(f"bystar2_auctionee@{DEFAULT_HOST}",   AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "bystar2_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_mazak    = Auctionee(f"mazak_auctionee@{DEFAULT_HOST}",    AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "mazak_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_eh       = Auctionee(f"eh_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "eh_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_inv1       = Auctionee(f"inv1_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "inv1_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_inv2       = Auctionee(f"inv2_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "inv2_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg1       = Auctionee(f"sg1_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg1_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg2       = Auctionee(f"sg2_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg2_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg3       = Auctionee(f"sg3_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg3_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg4       = Auctionee(f"sg4_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg4_device", "auction_operator": "auction_operator"}, verify_security=False)
    
    #ao = AuctionOperator(f"auctionoperator@{DEFAULT_HOST}", AGENT_PASSWORD, {"auctionees: ['pv_auctionee', 'bystar_auctionee', 'byprint_auctionee']"}, verify_security=False)
    ao = AuctionOperator(f"auction_operator@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)


    repeat = True
    while(repeat == True):
        try:
            # uruchamiamy agenta Predictor dla każdego urządzenia
            await prd_pv.start(auto_register=True)
            await prd_bystar1.start(auto_register=True)
            await prd_bystar2.start(auto_register=True)
            await prd_mazak.start(auto_register=True)
            await prd_eh.start(auto_register=True)
            await prd_inv1.start(auto_register=True)
            await prd_inv2.start(auto_register=True)
            await prd_sg1.start(auto_register=True)
            await prd_sg2.start(auto_register=True)
            await prd_sg3.start(auto_register=True)
            await prd_sg4.start(auto_register=True)
            
            # uruchamiamy agenta DeviceManager dla każdego urządzenia
            await dm_pv.start(auto_register=True)
            await dm_bystar1.start(auto_register=True)
            await dm_bystar2.start(auto_register=True)
            await dm_mazak.start(auto_register=True)
            await dm_eh.start(auto_register=True)
            await dm_inv1.start(auto_register=True)
            await dm_inv2.start(auto_register=True)
            await dm_sg1.start(auto_register=True)
            await dm_sg2.start(auto_register=True)
            await dm_sg3.start(auto_register=True)
            await dm_sg4.start(auto_register=True)

            # uruchamiamy agenta Auctionee dla każdego urządzenia
            await auc_pv.start(auto_register=True)
            await auc_bystar1.start(auto_register=True)
            await auc_bystar2.start(auto_register=True)
            await auc_mazak.start(auto_register=True)
            await auc_eh.start(auto_register=True)
            await auc_inv1.start(auto_register=True)
            await auc_inv2.start(auto_register=True)
            await auc_sg1.start(auto_register=True)
            await auc_sg2.start(auto_register=True)
            await auc_sg3.start(auto_register=True)
            await auc_sg4.start(auto_register=True)

            # uruchamiamy jednego AuctionOperator
            await ao.start(auto_register=True)
            
            repeat = False
            break

        except Exception as exception:
#            print(type(exception).__name__)
            print("Nie udało się zainicjować agentów probujemy dalej....")
            time.sleep(3)
            repeat = True

#    while True:
#        try:
#            await asyncio.sleep(60)
#        except:
#            break

if __name__ == "__main__":
    spade.run(main())

