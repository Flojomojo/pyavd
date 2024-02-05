# pyavd
A python wrapper for the avdmanager and emulator command line tool

Pyavd is a wrapper for the [avdmanager from google](https://developer.android.com/studio/command-line/avdmanager) and the commonly used [emulator from google](https://developer.android.com/studio/run/emulator-commandline). You can create, manage and start Android Virtual Devices (AVDs) using python.

# Requirements
- currently only linux is officially supported, but windows/macos might work as well
- installed android-sdk 

# Example 

```python
from time import sleep
import pyavd

# If the emulator/avdmanager executables are not in the path, include the following
#pyavd.pyavd.avd_cmd = "/path/to/avdmanager"
#pyavd.pyavd.emulator_cmd = "/path/to/emulator"

# Get all the avaliable devices
devices = pyavd.Device.get_devices()
    
# Declare a package and name
package = "system-images;android-32;google_apis;x86"

name = "created_with_pyavd"

# Create a avd with the declared variables and a chosen device
avd = pyavd.AVD.create(name, package, devices[22])

# Use a custom config
custom_config = "-no-snapshot"

# Start it in detached mode
p = avd.start(detach=True, config=custom_config)

sleep(10)

# After 10 seconds stop it again and delete it
avd.stop()

avd.delete()
```
