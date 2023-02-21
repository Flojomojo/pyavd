import time
import pyavd

#pyavd.pyavd.avd_cmd = "F:\\Programme\\AndroidSDK\\tools\\bin\\avdmanager.bat"
#pyavd.pyavd.emulator_cmd = "F:\\Programme\\AndroidSDK\\emulator\\emulator-arm.exe"

#targets = pyavd.get_targets()
#devices = pyavd.get_devices()
avds = pyavd.get_avds()
p = avds[1].start(detach=True, config="-no-snapshot")
print(type(p))
print("zzzzz")
avds[1].stop()