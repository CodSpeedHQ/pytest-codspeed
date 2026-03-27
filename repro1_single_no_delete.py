"""Test 1: Single instance, no explicit delete — crash at shutdown?"""
import os
os.environ["CODSPEED_ENV"] = "1"
from pytest_codspeed.instruments.hooks import InstrumentHooks

h = InstrumentHooks()
print(f"Created: {h.instance}")
print("Exiting (no explicit delete)...")
