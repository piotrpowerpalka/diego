import spade
import sys
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
from DeviceManager import *
from AuctionOperator import *
from Auctionee import *
from Predictor import *
from DummyBalancer import *
import time
import csv
import datetime
import os
import asyncio
import traceback
import sys

DEFAULT_HOST = "server_hello"
AGENT_PASSWORD = "electrum1@3"


async def main():

    #xxx = DummyBalancer(f"xxx@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)    

    # uruchamiamy tyle agentów DeviceManager ile urządzeń, wiążemy je (nazwą) z agentami Auctoinee
    prd_pv       = Predictor(f"pv_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "pv", verify_security=False)
    prd_bysprint = Predictor(f"bysprint_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "bysprint", verify_security=False)
    prd_bystar1  = Predictor(f"bystar1_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "bystar1", verify_security=False)
    prd_bystar2  = Predictor(f"bystar2_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "bystar2", verify_security=False)
    prd_mazak    = Predictor(f"mazak_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "mazak", verify_security=False)
    prd_eh       = Predictor(f"eh_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "eh", verify_security=False)
    prd_inv1     = Predictor(f"inv1_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "inv1", verify_security=False)
    prd_inv2     = Predictor(f"inv2_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "inv2", verify_security=False)
    prd_sg1     = Predictor(f"sg1_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg1", verify_security=False)
    prd_sg2     = Predictor(f"sg2_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg2", verify_security=False)
    prd_sg3     = Predictor(f"sg3_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg3", verify_security=False)
    prd_sg4     = Predictor(f"sg4_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg4", verify_security=False)
    prd_evcs    = Predictor(f"evcs_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "evcs", verify_security=False)
    prd_SOC     = Predictor(f"soc_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "soc", verify_security=False)
    prd_sg1prim = Predictor(f"sg1prim_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "sg1prim", verify_security=False)
    prd_MS      = Predictor(f"ms_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "ms", verify_security=False)
    prd_network = Predictor(f"network_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, "network", verify_security=False)
    
    # uruchamiamy tyle agentów DeviceManager ile urządzeń, wiążemy je (nazwą) z agentami Auctoinee
    dm_pv       = DeviceManager(f"pv_device@{DEFAULT_HOST}",        AGENT_PASSWORD, "pv", {"predictor": "pv_predictor", "auctionee": "pv_auctionee"}, verify_security=False)
    dm_bysprint = DeviceManager(f"bysprint_device@{DEFAULT_HOST}",  AGENT_PASSWORD, "bysprint", {"predictor": "bysprint_predictor", "auctionee": "bysprint_auctionee"}, verify_security=False)
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
    dm_evcs    = DeviceManager(f"evcs_device@{DEFAULT_HOST}",      AGENT_PASSWORD, "evcs", {"predictor": "evcs_predictor", "auctionee": "evcs_auctionee"}, verify_security=False)
    dm_SOC     = DeviceManager(f"soc_device@{DEFAULT_HOST}",       AGENT_PASSWORD, "soc", {"predictor": "soc_predictor", "auctionee": "soc_auctionee"}, verify_security=False)
    dm_sg1prim = DeviceManager(f"sg1prim_device@{DEFAULT_HOST}",   AGENT_PASSWORD, "sg1prim", {"predictor": "sg1prim_predictor", "auctionee": "sg1prim_auctionee"}, verify_security=False)
    dm_MS      = DeviceManager(f"ms_device@{DEFAULT_HOST}",        AGENT_PASSWORD, "ms", {"predictor": "ms_predictor", "auctionee": "ms_auctionee"}, verify_security=False)
    dm_network = DeviceManager(f"network_device@{DEFAULT_HOST}",        AGENT_PASSWORD, "network", {"predictor": "network_predictor", "auctionee": "network_auctionee"}, verify_security=False)
    
    # uruchamiamy tyle agentów Auctionee ile urządzeń
    auc_pv = Auctionee(f"pv_auctionee@{DEFAULT_HOST}",              AGENT_PASSWORD, {"active": "not_controllable", "reactive": "controllable", "device_manager": "pv_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_bysprint = Auctionee(f"bysprint_auctionee@{DEFAULT_HOST}",  AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "bysprint_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_bystar1  = Auctionee(f"bystar1_auctionee@{DEFAULT_HOST}",   AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "bystar1_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_bystar2  = Auctionee(f"bystar2_auctionee@{DEFAULT_HOST}",   AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "bystar2_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_mazak    = Auctionee(f"mazak_auctionee@{DEFAULT_HOST}",     AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "mazak_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_eh       = Auctionee(f"eh_auctionee@{DEFAULT_HOST}",        AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "eh_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_inv1     = Auctionee(f"inv1_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "inv1_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_inv2     = Auctionee(f"inv2_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "inv2_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg1       = Auctionee(f"sg1_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg1_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg2       = Auctionee(f"sg2_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg2_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg3       = Auctionee(f"sg3_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg3_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg4       = Auctionee(f"sg4_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg4_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_evcs      = Auctionee(f"evcs_auctionee@{DEFAULT_HOST}",     AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "evcs_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_SOC       = Auctionee(f"soc_auctionee@{DEFAULT_HOST}",      AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "soc_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_sg1prim   = Auctionee(f"sg1prim_auctionee@{DEFAULT_HOST}",  AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "sg1prim_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_MS        = Auctionee(f"ms_auctionee@{DEFAULT_HOST}",       AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "ms_device", "auction_operator": "auction_operator"}, verify_security=False)
    auc_network   = Auctionee(f"network_auctionee@{DEFAULT_HOST}",  AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "network_device", "auction_operator": "auction_operator"}, verify_security=False)

    #ao = AuctionOperator(f"auctionoperator@{DEFAULT_HOST}", AGENT_PASSWORD, {"auctionees: ['pv_auctionee', 'bystar_auctionee', 'byprint_auctionee']"}, verify_security=False)
    ao = AuctionOperator(f"auction_operator@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)


    repeat = True
    while(repeat == True):
        try:
            # await xxx.start(auto_register=True)
            # uruchamiamy agenta Predictor dla każdego urządzenia
            await prd_pv.start(auto_register=True)          # ok
            
            await prd_bysprint.start(auto_register=True)    # ok
            
            await prd_bystar1.start(auto_register=True)     # ok
            
            await prd_bystar2.start(auto_register=True)     # ok
            
            await prd_mazak.start(auto_register=True)       # ok
            
            await prd_eh.start(auto_register=True)          # ok
            
            await prd_inv1.start(auto_register=True)        # ok
            
            await prd_inv2.start(auto_register=True)        # ok
            
            await prd_sg1.start(auto_register=True)         # ok
            
            await prd_sg2.start(auto_register=True)         # ok
            
            await prd_sg3.start(auto_register=True)         # ok
            
            await prd_sg4.start(auto_register=True)         # ok
            
            await prd_evcs.start(auto_register=True)        # ok
            
            await prd_SOC.start(auto_register=True)
            
            await prd_sg1prim.start(auto_register=True)     # ok
            
            await prd_MS.start(auto_register=True)
            
            await prd_network.start(auto_register=True)     # ok
            
            
            # # uruchamiamy agenta DeviceManager dla każdego urządzenia
            await dm_pv.start(auto_register=True)
            
            await dm_bysprint.start(auto_register=True)
            
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
            
            await dm_evcs.start(auto_register=True)
            
            await dm_SOC.start(auto_register=True)
            
            await dm_sg1prim.start(auto_register=True)
            
            await dm_MS.start(auto_register=True)
            
            await dm_network.start(auto_register=True)
            
            # # uruchamiamy agenta Auctionee dla każdego urządzenia
            await auc_pv.start(auto_register=True)
            
            await auc_bysprint.start(auto_register=True)
            
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
            
            await auc_evcs.start(auto_register=True)
            
            await auc_SOC.start(auto_register=True)
            
            await auc_sg1prim.start(auto_register=True)
            
            await auc_MS.start(auto_register=True)
            
            await auc_network.start(auto_register=True)
            
            # # uruchamiamy jednego AuctionOperator
            await ao.start(auto_register=True)
            
            repeat = False
            break

        except Exception as exception:
#            print(type(exception).__name__)
            print("Nie udało się zainicjować agentów probujemy dalej....")
            time.sleep(3)
            repeat = True

    while True:
        try:
            await asyncio.sleep(60)
        except Exception as exception:
            print(traceback.format_exc()) # This line is for getting traceback.
            print(sys.exc_info()[2]) # This line is getting for the error type.            break

if __name__ == "__main__":
    spade.run(main())

