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
    prd_pv      = Predictor(f"pv_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)
    prd_bystar  = Predictor(f"bystar_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)
    prd_byprint = Predictor(f"byprint_predictor@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)

    # uruchamiamy tyle agentów DeviceManager ile urządzeń, wiążemy je (nazwą) z agentami Auctoinee
    dm_pv      = DeviceManager(f"pv_device@{DEFAULT_HOST}", AGENT_PASSWORD, {"predictor": "pv_predictor", "auctionee": "pv_auctionee"}, verify_security=False)
    dm_bystar  = DeviceManager(f"bystar_device@{DEFAULT_HOST}", AGENT_PASSWORD, {"predictor": "bystar_predictor", "auctionee": "bystar_auctionee"}, verify_security=False)
    dm_byprint = DeviceManager(f"byprint_device@{DEFAULT_HOST}", AGENT_PASSWORD, {"predictor": "byprint_predictor", "auctionee": "byprint_auctionee"}, verify_security=False)
    
    # uruchamiamy tyle agentów Auctionee ile urządzeń
    auc_pv = Auctionee(f"pv_auctionee@{DEFAULT_HOST}", AGENT_PASSWORD, {"active": "not_controllable", "reactive": "controllable", "device_manager": "pv_device"}, verify_security=False)
    auc_bystar = Auctionee(f"bystar_auctionee@{DEFAULT_HOST}", AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "bystar_device"}, verify_security=False)
    auc_byprint = Auctionee(f"byprint_auctionee@{DEFAULT_HOST}", AGENT_PASSWORD, {"active": "not_controllable", "reactive": "not_controllable", "device_manager": "byprint_device"}, verify_security=False)

    #ao = AuctionOperator(f"auctionoperator@{DEFAULT_HOST}", AGENT_PASSWORD, {"auctionees: ['pv_auctionee', 'bystar_auctionee', 'byprint_auctionee']"}, verify_security=False)
    ao = AuctionOperator(f"auctionoperator@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)


    repeat = True
    while(repeat == True):
        try:
            # uruchamiamy agenta Predictor dla każdego urządzenia
            await prd_pv.start(auto_register=True)
            await prd_bystar.start(auto_register=True)
            await prd_byprint.start(auto_register=True)

            # uruchamiamy agenta DeviceManager dla każdego urządzenia
            await dm_pv.start(auto_register=True)
            await dm_bystar.start(auto_register=True)
            await dm_byprint.start(auto_register=True)

            # uruchamiamy agenta Auctionee dla każdego urządzenia
            await auc_pv.start(auto_register=True)
            await auc_bystar.start(auto_register=True)
            await auc_byprint.start(auto_register=True)

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

