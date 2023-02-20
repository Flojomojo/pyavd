import re
import os
import subprocess

avd_cmd = "avdmanager"

class Target:
    def __init__(self, id: int, id_alias: str, name: str, type: str, api_level: int, revision: int) -> None:
        self.id = id
        self.id_alias = id_alias
        self.name = name
        self.type = type
        self.api_level = api_level
        self.revision = revision

    def isEmpty(self):
        return self.id == -1

    def __init__(self) -> None:
        self.id = -1
        pass
        
class Device:
    def __init__(self, id: int, id_alias: str, name: str, oem: str, tag: str="") -> None:
        self.id = id
        self.id_alias = id_alias
        self.name = name
        self.oem = oem
        self.tag = tag

    def isEmpty(self):
        return self.id == -1

    def __init__(self) -> None:
        self.id = -1
        self.tag = ""
        pass

class AVD:
    def __init__(self, name: str, device: Device, path: str, target: str, skin: str, sdcard_size: str, based_on: str, abi: str) -> None:
        self.name = name
        self._device = device
        # Check if path exists
        if( not os.path.isfile(path)):
            raise Exception("Path does not exist")
        self.path = path
        self.target = target
        self.skin = skin
        self.sdcard_size = sdcard_size
        self.based_on = based_on
        self.abi = abi

    def isEmpty(self):
        return self.name == "invalid"

    def __init__(self) -> None:
        self._device = None
        self.name = "invalid"

    @property
    def device(self):
        return self._device
    
    @device.getter
    def device(self):
        return self._device

    @device.setter
    def device(self, device: str):
        # Remove everything inside the parentheses so we can actually compare it 
        device = re.sub("[\(\[].*?[\)\]]", "", device).strip()
        # Find the corrent device to the string
        for d in get_devices():
            if(d.id_alias == device):
                self._device = d
                return

    def delete(self) -> bool:
        cmd_args = [avd_cmd, "delete", "avd", "-n", self.name]
        try: 
            res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise Exception("Could not find avdmanager")
        return res.stdout and not res.stderr
    
    def move(self, new_path: str):
        print("I cant figure this out yet")
        return
        filename = os.path.basename(self.path)
        new_path = os.path.join(new_path.strip(), filename)
        cmd_args = [avd_cmd, "move", "avd", "-n", self.name, "-p", new_path]
        try: 
            res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise Exception("Could not find avdmanager")
        print(cmd_args)
        if res.stdout:
            print(res)
            self.path = new_path

    def rename(self, new_name: str) -> bool:
        cmd_args = [avd_cmd, "move", "avd", "-n", self.name, "-r", new_name]
        try: 
            res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise Exception("Could not find avdmanager")
        if res.stdout and not res.stderr:
            # Correct the filename and filepath to the new filename and path
            self.name = new_name
            self.path = os.path.join(os.path.dirname(os.path.abspath(self.path)), self.name + ".avd")
            return True
        return False

    def start(self):
        pass

def get_targets() -> list[Target]:
    cmd_args = [avd_cmd, "list", "target"]
    try: 
        res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise Exception("Could not find avdmanager")

    targets = []
    # Parse devices from output
    if res.stdout:
        current_target = Target()
        for line in res.stdout.decode("utf-8").split(os.linesep):
            stripped_line = line.strip()
            if(not stripped_line):
                continue

            # If "----------" is seen a new target definition begins
            # So we add the old current target and overwrite it
            if(stripped_line == "----------"):
                if(not current_target.isEmpty()):
                    targets.append(current_target)
                current_target = Target()
                continue
            
            # If there is no : in the line, its not a valid key value pair
            if(":" not in stripped_line):
                continue

            key, value = stripped_line.split(":")
            key = key.strip().upper()
            value = value.strip()
            if(key == "id".upper()):
                id, alias = value.split(" or ")
                current_target.id = int(id.strip())
                current_target.id_alias = alias.strip().replace('"', '')
            elif(key == "Name".upper()):
                current_target.name = value
            elif(key == "Type".upper()):
                current_target.type = value
            elif(key == "API Level".upper()):
                current_target.api_level = int(value)
            elif(key == "Revision".upper()):
                current_target.revision = int(value)

        # Add the last target
        if(not current_target.isEmpty()):
            targets.append(current_target)  
    return targets

def get_devices() -> list[Device]:
    cmd_args = [avd_cmd, "list", "device"]
    try: 
        res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise Exception("Could not find avdmanager")

    devices = []
    # Parse devices from output
    if res.stdout:
        current_device = Device()
        for line in res.stdout.decode("utf-8").split(os.linesep):
            stripped_line = line.strip()
            if(not stripped_line):
                continue
            # If "---------" is seen a new target definition begins
            # So we add the old current target and overwrite it
            if(stripped_line == "---------"):
                if(not current_device.isEmpty()):
                    devices.append(current_device)
                current_device = Device()
                continue
            
            # If there is no : in the line, its not a valid key value pair
            if(":" not in stripped_line):
                continue

            key, value = stripped_line.split(":")
            key = key.strip().upper()
            value = value.strip()

            if(key == "id".upper()):
                id, alias = value.split(" or ")
                current_device.id = int(id.strip())
                current_device.id_alias = alias.strip().replace('"', '')
            elif(key == "Name".upper()):
                current_device.name = value
            elif(key == "OEM".upper()):
                current_device.oem = value
            elif(key == "Tag".upper()):
                current_device.tag = value

        # Append last device
        if(not current_device.isEmpty()):
            devices.append(current_device)
    
    return devices

def get_avds():
    cmd_args = [avd_cmd, "list", "avd"]
    try: 
        res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise Exception("Could not find avdmanager")

    avds = []
    # Parse avds from output
    if res.stdout:
        current_avd = AVD()
        for line in res.stdout.decode("utf-8").split(os.linesep):
            stripped_line = line.strip()
            if(not stripped_line):
                continue
            # If "---------" is seen a new target definition begins
            # So we add the old current target and overwrite it
            if(stripped_line == "---------"):
                if(not current_avd.isEmpty()):
                    avds.append(current_avd)
                current_avd = AVD()
                continue
            
            # If there is no : in the line, its not a valid key value pair
            if(":" not in stripped_line):
                continue

            key, value, *rest = stripped_line.split(":")
            key = key.strip().upper()
            value = value.strip()   
            if(key == "Name".upper()):
                current_avd.name = value
            elif(key == "Device".upper()):
                current_avd.device = value
            elif(key == "Path".upper()):
                current_avd.path = value
            elif(key == "Target".upper()):
                current_avd.target = value
            elif(key == "Skin".upper()):
                current_avd.skin = value
            elif(key == "Sdcard".upper()):
                current_avd.sdcard_size = value
            elif(key == "Based on".upper()):
                # Based on: Android 12L (Sv2) Tag/ABI: google_apis/x86_64
                current_avd.based_on = value.replace("Tag/ABI", "").strip()
                current_avd.abi = rest[0].strip()
    
        # Append last avd
        if(not current_avd.isEmpty()):
            avds.append(current_avd)

    return avds

def create_avd(name, package, force=False, device=None, sdcard=None, tag=None, skin=None, abi=None, path=None):
    inclusion_dict = {
        "--device": device,
        "--sdcard": sdcard,
        "--tag": tag,
        "--skin": skin,
        "--abi": abi,
        "--path": path,
    }
    cmd_args = [avd_cmd, "create", "avd", "-n", name, "--package", package, "--force", force]
    for key, value in inclusion_dict.items():
        if(value):
            cmd_args.append(key)
            cmd_args.append(value)
    print(cmd_args)
    return
    try: 
        res = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise Exception("Could not find avdmanager")



