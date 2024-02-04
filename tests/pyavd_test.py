import sys
import pytest
sys.path.append("../pyavd/")
from pyavd import get_targets, get_avds, get_devices, create_avd, get_avd_by_name

#from ..pyavd import get_targets, get_avds, get_devices, create_avd, get_avd_by_name

AVD_NAME = "test_avd"

def test_get_targets():
    targets = get_targets()
    print(targets)
    assert True

def test_create_avd():
    devices = get_devices()
    created = create_avd(AVD_NAME, "system-images;android-30;google_apis;x86", devices[0])
    assert created is not None
    # Check if it actually got created
    searched = get_avd_by_name(AVD_NAME)
    assert searched is not None
    assert searched == created

def test_get_avds():
    # Get the avds and check if it contains "test_avd"
    avds = get_avds()
    for avd in avds:
        if avd.name == AVD_NAME:
            assert True
            return
    assert False

def test_delete_avd():
    # Get the avd and delete it
    avd_to_delete = get_avd_by_name(AVD_NAME)
    assert avd_to_delete is not None
    avd_to_delete.delete()
    # Try to get it again and see if it exists
    hopefully_deleted_avd = get_avd_by_name(AVD_NAME)
    assert hopefully_deleted_avd is None

