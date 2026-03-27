"""Test 2: Single instance, explicit deinit + del — crash?"""
import os
os.environ["CODSPEED_ENV"] = "1"
from pytest_codspeed.instruments.hooks import InstrumentHooks

h = InstrumentHooks()
print(f"Created: {h.instance}")
h.lib.instrument_hooks_deinit(h.instance)
print("Deinited explicitly")
del h
print("Deleted, exiting...")
