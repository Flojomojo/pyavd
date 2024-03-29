# TODO remove in future versions
from __future__ import annotations
import re
import os
import shlex
import subprocess
import logging

avd_cmd = "avdmanager"
emulator_cmd = "emulator"
adb_cmd = "adb"


class Target:
    def __init__(self,
                 id: int = -1,
                 id_alias: str | None = None,
                 name: str | None = None,
                 target_type: str | None = None,
                 api_level: int | None = None,
                 revision: int | None = None) -> None:
        self.id = id
        self.id_alias = id_alias
        self.name = name
        self.target_type = target_type
        self.api_level = api_level
        self.revision = revision

    def is_empty(self) -> bool:
        """
        Returns: True if the Target is empty
        """
        return self.id == -1

    @classmethod
    def get_targets(cls) -> list[Target]:
        """
        Get a list of all available targets

        Raises:
            Exception: If avdmanager is not found

        Returns:
            list[Target]: List of all available targets
        """
        cmd_args = ["list", "target"]
        res = _execute_avd_command(cmd_args)

        targets = []
        # Parse devices from output
        if res.stdout:
            current_target = Target()
            for line in res.stdout.decode("utf-8").split("\n"):
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                # If "----------" is seen, a new target definition begins
                # So we add the current target to the targets and start a new one
                if stripped_line == "----------":
                    if not current_target.is_empty():
                        targets.append(current_target)
                    current_target = Target()
                    continue

                # If there is no : in the line, its not a valid key value pair
                if ":" not in stripped_line:
                    continue

                key, value = stripped_line.split(":")
                key = key.strip().upper()
                value = value.strip()
                # TODO match?
                if key == "id".upper():
                    id, alias = value.split(" or ")
                    current_target.id = int(id.strip())
                    current_target.id_alias = alias.strip().replace('"', '')
                elif key == "Name".upper():
                    current_target.name = value
                elif key == "Type".upper():
                    current_target.target_type = value
                elif key == "API Level".upper():
                    current_target.api_level = int(value)
                elif key == "Revision".upper():
                    current_target.revision = int(value)

            # Add the last target
            if not current_target.is_empty():
                targets.append(current_target)
        return targets


class Device:
    def __init__(self,
                 id: int = -1,
                 id_alias: str | None = None,
                 name: str | None = None,
                 oem: str | None = None,
                 tag: str = "") -> None:
        self.id = id
        self.id_alias = id_alias
        self.name = name
        self.oem = oem
        self.tag = tag

    def is_empty(self) -> bool:
        """
        Returns: True if the Device is empty
        """
        return self.id == -1

    @classmethod
    def get_devices(cls) -> list[Device]:
        """
        Get a list of all available devices

        Raises:
            Exception: If avdmanager is not found

        Returns:
            list[Device]: List of all available devices
        """
        cmd_args = ["list", "device"]
        res = _execute_avd_command(cmd_args)

        devices = []
        # Parse devices from output
        if res.stdout:
            current_device = Device()
            for line in res.stdout.decode("utf-8").split("\n"):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                # If "---------" is seen a new target definition begins
                # So we add the old current target and overwrite it
                if stripped_line == "---------":
                    if not current_device.is_empty():
                        devices.append(current_device)
                    current_device = Device()
                    continue

                # If there is no : in the line, its not a valid key value pair
                if ":" not in stripped_line or stripped_line.count(":") > 2:
                    continue
                key, value = stripped_line.split(":")
                key = key.strip().upper()
                value = value.strip()

                # TODO match?
                if key == "id".upper():
                    id, alias = value.split(" or ")
                    current_device.id = int(id.strip())
                    current_device.id_alias = alias.strip().replace('"', '')
                elif key == "Name".upper():
                    current_device.name = value
                elif key == "OEM".upper():
                    current_device.oem = value
                elif key == "Tag".upper():
                    current_device.tag = value

            # Append last device
            if not current_device.is_empty():
                devices.append(current_device)

        return devices

class AVD:
    def __init__(self, 
                 name: str = "invalid",
                 device: Device | None = None,
                 path: str | None = None,
                 target: str | None = None,
                 skin: str | None = None,
                 sdcard_size: str | None = None,
                 based_on: str | None = None,
                 abi: str | None = None) -> None:
        self.name = name
        self._device = device
        # Check if path exists
        if path is not None and not os.path.isfile(path):
            raise Exception("Path does not exist")
        self.path = path
        self.target = target
        self.skin = skin
        self.sdcard_size = sdcard_size
        self.based_on = based_on
        self.abi = abi
        self.process = None

    def __eq__(self, __value: object) -> bool:
        return (isinstance(__value, self.__class__)
                and __value.name == self.name
                and __value.process == self.process)

    def is_empty(self) -> bool:
        """
        Returns:
            True if the AVD is empty
        """
        return self.name == "invalid"

    @property
    def device(self) -> Device | None:
        return self._device

    @device.getter
    def device(self) -> Device | None:
        return self._device

    @device.setter
    def device(self, device: str):
        # Remove everything inside the parentheses so we can actually compare it
        device = re.sub(r"[\(\[].*?[\)\]]", "", device).strip()
        # Find the corrent device to the string
        for d in Device.get_devices():
            if d.id_alias == device:
                self._device = d
                return

    @classmethod
    def create(cls,
                   name: str, 
                   package: str,
                   device: Device,
                   force: bool = False,
                   sdcard: str | None = None,
                   tag: str | None = None,
                   skin: str | None = None,
                   abi: str | None = None,
                   path: str | None = None) -> AVD:
        """
        Create a new AVD with the given name and package

        Args:
            name (str): Name of the new AVD
            package (str): Package path of the system image for this AVD (e.g. 'system-images;android-19;google_apis;x86')
            device (str): The device which the emulator is based on
            force (bool, optional): Forces creation (overwrites an existing AVD). Defaults to False.
            sdcard (str, optional): Path to a shared SD card image, or size of a new sdcard for the new AVD. Defaults to None.
            tag (str, optional): The sys-img tag to use for the AVD. The default is to auto-select if the platform has only one tag for its system images. Defaults to None.
            skin (str, optional): Skin of the AVD. Defaults to None.
            abi (str, optional): The ABI to use for the AVD. The default is to auto-select the ABI if the platform has only one ABI for its system images. Defaults to None.
            path (str, optional): Directory where the new AVD will be created. Defaults to None.

        Raises:
            Exception: If avdmanager is not found

        Returns:
            AVD: The newly created AVD or None if there was an error
        """
        inclusion_dict = {
            "--sdcard": sdcard,
            "--tag": tag,
            "--skin": skin,
            "--abi": abi,
            "--path": path,
        }
        cmd_args = ["create", "avd", "-n",
                    name, "--package", package, "--device", str(device.id)]
        for key, value in inclusion_dict.items():
            if value:
                cmd_args.append(key)
                cmd_args.append(str(value))
        if force:
            cmd_args += "--force"
        res = _execute_avd_command(cmd_args)
        # Check stderr
        if res.stderr.decode() != "":
            logging.warning(res.stderr.decode())
        created_avd = cls.get_by_name(name)
        assert created_avd is not None, "Avd was not created"
        return created_avd

    @classmethod
    def get_by_name(cls, name: str) -> AVD | None:
        """
        Get a avd by its name

        Args:
            name: The name of the avd

        Returns:
            AVD | None: The avd if one was found, None otherwise
        """
        for avd in cls.get_avds():
            if avd.name == name:
                return avd
        return None

    @classmethod
    def get_avds(cls) -> list[AVD]:
        """
        Get a list of all available AVDs

        Raises:
            Exception: If avdmanager is not found

        Returns:
            list[AVD]: List of all available AVDs
        """
        cmd_args = ["list", "avd"]
        res = _execute_avd_command(cmd_args)

        avds = []
        # Parse avds from output
        if res.stdout:
            current_avd = AVD()
            for line in res.stdout.decode("utf-8").split("\n"):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                # If "---------" is seen, a new target definition begins
                # So we add the old current target to the list and start a new one
                if stripped_line == "---------":
                    if not current_avd.is_empty():
                        avds.append(current_avd)
                    current_avd = AVD()
                    continue

                # If there is no : in the line, its not a valid key value pair
                if ":" not in stripped_line:
                    continue

                key, value, *rest = stripped_line.split(":")
                key = key.strip().upper()
                value = value.strip()
                # TODO match?
                if key == "Name".upper():
                    current_avd.name = value
                elif key == "Device".upper():
                    current_avd.device = value
                elif key == "Path".upper():
                    current_avd.path = value
                elif key == "Target".upper():
                    current_avd.target = value
                elif key == "Skin".upper():
                    current_avd.skin = value
                elif key == "Sdcard".upper():
                    current_avd.sdcard_size = value
                elif key == "Based on".upper():
                    # Based on: Android 12L (Sv2) Tag/ABI: google_apis/x86_64
                    current_avd.based_on = value.replace("Tag/ABI", "").strip()
                    current_avd.abi = rest[0].strip()

            # Append last avd
            if not current_avd.is_empty():
                avds.append(current_avd)

        return avds

    def delete(self) -> bool:
        """
        Deletes the avd

        Raises:
            Exception: If the avdmanager could not be found

        Returns:
            True if successful
        """
        cmd_args = ["delete", "avd", "-n", self.name]
        res = _execute_avd_command(cmd_args)
        # TODO ?
        return res.stdout and not res.stderr

    def move(self, new_path: str) -> bool:
        """
        Move the AVD to a new path

        Args:
            new_path (str): New path to move the AVD to

        Raises:
            Exception: If avdmanager is not found

        Returns:
            bool: True if the move was successful, False otherwise
        """
        raise NotImplementedError("This functionality does not seem to work using the avdmanager")
        cmd_args = ["move", "avd", "-n", self.name, "-p", new_path]
        res = _execute_avd_command(cmd_args)
        if res.stdout and not res.stderr:
            self.path = new_path
            return True
        return False

    def rename(self, new_name: str) -> bool:
        """
        Rename the AVD

        Args:
            new_name (str): New name for the AVD

        Raises:
            Exception: If avdmanager is not found

        Returns:
            bool: True if the rename was successful, False otherwise
        """
        cmd_args = ["move", "avd", "-n", self.name, "-r", new_name]
        res = _execute_avd_command(cmd_args)
        if res.stdout and not res.stderr:
            # Correct the filename and filepath to the new filename and path
            self.name = new_name
            # TODO better paths
            self.path = os.path.join(os.path.dirname(
                os.path.abspath(self.path)), self.name + ".avd")
            return True
        self.name = new_name
        return False

    def start(self, detach: bool = False, config: str = "") -> subprocess.Popen:
        """
        Start the AVD

        Args:
            detach (bool, optional): Detach process. Defaults to False.
            config (str, optional): Custom config string. Defaults to "".

        Raises:
            Exception: If emulator is not found
            subprocess.TimeoutExpired: If the emulator times out
            Exception: If the process could not be found

        Returns:
            subprocess.Popen: The process of the emulator
        """
        cmd_args = [emulator_cmd, "-avd", self.name]
        proc = None
        if config:
            cmd_args += shlex.split(config)
        try:
            proc = subprocess.Popen(
                cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # The emulator needs a second to load, so we wait a second if we want to detach
            if detach:
                proc.wait(1)
            else:
                proc.wait()
        except OSError:
            raise Exception("Could not find emulator")
        except subprocess.TimeoutExpired:
            if not detach:
                raise
        if proc is None:
            raise Exception("Could not get process")
        self.process = proc
        return proc

    def stop(self, port:int = 5554) -> bool:
        """
        Stops the emulator via adb

        Args:
            port (int, optional): The port of the emulator. Defaults to 5554.

        Returns:
            bool: True if the emulator has been stopped. False otherwise.
        """
        emulator_name = f"emulator-{port}"
        cmd_args = ["-s", emulator_name, "emu", "kill"]
        result = _execute_adb_command(cmd_args)
        # TODO actually check output 
        return True

    def kill(self) -> bool:
        """
        Kills the AVD
        Note: Preferably use stop()

        Returns:
            bool: True if the emulator was stopped, False otherwise
        """
        if not self.process:
            return False
        self.process.kill()
        # Wait for zombie process to exit
        self.process.wait()
        self.process = None
        return True

def _execute_command(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    """
    Executes a command 
    Args:
        command (list[str): The command represented as a list of command args, e.g. ["ls", "-l"]

    Returns:
        The result of the command as a CompletedProcess obj
    """
    res = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("command", command, "res:", res.stdout, res.stderr)
    return res

def _execute_avd_command(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """
    Executes a avd command
    Args:
        args: The args of the avd command, e.g. ["list", "avd"] will execute `avdmanager list avd` 

    Returns:
        The result of the avd command as a CompletedProcess obj
    """
    return _execute_command([avd_cmd] + args)

def _execute_adb_command(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """
    Executes a adb command
    Args:
        args: The args of the adb command, e.g. ["devices"] will execute `adb devices` 

    Returns:
        The result of the avd command as a CompletedProcess obj
    """
    return _execute_command([adb_cmd] + args)

