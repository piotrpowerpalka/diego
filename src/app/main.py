import time
import asyncio
import traceback
import sys
import spade
from spade.agent import Agent

from agents.device_manager import DeviceManager
from agents.auction_operator import AuctionOperator
from agents.auctionee import Auctionee
from agents.predictor import Predictor

from api.requests import fetch_devices
from helpers import get_devices_list
from settings import USE_CSV, DEBUG


async def main():

    device_list = get_devices_list() if USE_CSV else await fetch_devices()

    predictor_instances = {}
    manager_instances = {}
    auctionee_instances = {}

    for device_name in device_list:
        # init predictor for each device
        predictor_instances[device_name] = Predictor(device_name)
        # init device manager for each device
        manager_instances[device_name] = DeviceManager(device_name)
        # init auctionee for each device
        auctionee_instances[device_name] = Auctionee(device_name, "auction_operator")

    operator = AuctionOperator("auction_operator", device_list)

    repeat = True
    while repeat == True:
        try:
            # Start all Predictor instances
            for predictor in predictor_instances.values():
                if isinstance(predictor, Agent) and not predictor.is_alive():
                    await predictor.start()

            # Start all DeviceManager instances
            for manager in manager_instances.values():
                if isinstance(manager, Agent) and not manager.is_alive():
                    await manager.start()

            # Start all Auctionee instances
            for auctionee in auctionee_instances.values():
                if isinstance(auctionee, Agent) and not auctionee.is_alive():
                    await auctionee.start()

            # # uruchamiamy jednego AuctionOperator
            if not operator.is_alive():
                await operator.start()

            repeat = False
            break

        except Exception as exception:
            print("Failed to initiate agents. Try again ....")
            print(exception)
            time.sleep(3)
            repeat = True

    while True:
        try:
            await asyncio.sleep(60)
        except Exception as exception:
            print(traceback.format_exc())  # This line is for getting traceback.
            print(
                sys.exc_info()[2]
            )  # This line is getting for the error type.            break


if __name__ == "__main__":
    spade.run(main())
