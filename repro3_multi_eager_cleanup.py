"""Test 3: Multiple instances, explicit deinit before exit — does eager cleanup fix it?"""
import os
os.environ["CODSPEED_ENV"] = "1"
from pytest_codspeed.instruments.hooks import InstrumentHooks

instances = []
for i in range(5):
    h = InstrumentHooks()
    print(f"Created instance {i}: {h.instance}")
    instances.append(h)

for i, h in enumerate(instances):
    h.lib.instrument_hooks_deinit(h.instance)
    # Prevent __del__ from calling deinit again
    del h.instance
    del h.lib
    print(f"Cleaned up instance {i}")

del instances
print("Exiting...")
