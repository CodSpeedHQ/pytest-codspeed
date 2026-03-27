import os
os.environ["CODSPEED_ENV"] = "1"

from pytest_codspeed.instruments.hooks import InstrumentHooks

for i in range(5):
    h = InstrumentHooks()
    print(f"Created instance {i}: {h.instance}")

del h
print("Exiting...")
