from iqoptionapi.stable_api import IQ_Option
from dotenv import load_dotenv
import os
import time

load_dotenv()
api = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
api.connect()
time.sleep(2)
profits = api.get_all_profit()

print("EURUSD profit:")
if "EURUSD" in profits:
    print(profits["EURUSD"])
else:
    print("EURUSD not in profits")

print("EURUSD-OTC profit:")
if "EURUSD-OTC" in profits:
    print(profits["EURUSD-OTC"])
else:
    print("EURUSD-OTC not in profits")
