"""Test 4: Multiple instances, skip deinit entirely — confirm deinit is the crash site."""
import os
os.environ["CODSPEED_ENV"] = "1"
from pytest_codspeed.instruments.hooks import InstrumentHooks

# Monkey-patch __del__ to do nothing
InstrumentHooks.__del__ = lambda self: print(f"Skipping deinit for {self.instance}")

for i in range(5):
    h = InstrumentHooks()
    print(f"Created instance {i}: {h.instance}")

print("Exiting (deinit skipped)...")
