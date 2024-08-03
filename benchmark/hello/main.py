import spade
import sys
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import OneShotBehaviour
from AuctionOperator import *
from Auctionee import *
import time
import csv
import datetime
import os
import asyncio

DEFAULT_HOST = "server_hello"
AGENT_PASSWORD = "123456789"


async def main():
    print("Program starts running")
    pv_auc = Auctionee(f"pv_auctionee@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)
    ao = AuctionOperator(f"auctionoperator@{DEFAULT_HOST}", AGENT_PASSWORD, verify_security=False)
    repeat = True
    
    while(repeat == True):
        try:
            await pv_auc.start(auto_register=True)
            await ao.start(auto_register=True)
            
            repeat = False
            break

        except Exception as exception:
            print(type(exception).__name__)
            print("Nie udało się zainicjować agenta AO, probujemy dalej....")
            time.sleep(1)
            repeat = True

#    while True:
#        try:
#            await asyncio.sleep(60)
#        except:
#            break

if __name__ == "__main__":
    spade.run(main())

