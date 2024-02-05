import sys
import pytest

sys.path.append("../pyavd/")
from pyavd import *

# This import is for syntax highlighting
#from ..pyavd import * 

AVD_NAME = "test_avd"

def test_get_targets():
    targets = Target.get_targets()
    assert True

def test_create_avd():
    devices = Device.get_devices()
    created = AVD.create(AVD_NAME, "system-images;android-30;google_apis;x86", devices[0])
    assert created is not None
    # Check if it actually got created
    searched = AVD.get_by_name(AVD_NAME)
    assert searched is not None
    assert searched == created

@pytest.mark.skip(reason="Method does not work yet")
def test_move():
    avd = AVD.get_by_name(AVD_NAME)
    assert avd is not None
    old_path = avd.path
    new_path = "./test_avd.avd"
    avd.move(new_path)
    print("new path", avd.path)
    assert False

def test_empty_classes():
    assert AVD().is_empty()
    assert Device().is_empty()
    assert Target().is_empty()

def test_get_avds():
    # Get the avds and check if it contains "test_avd"
    avds = AVD.get_avds()
    for avd in avds:
        if avd.name == AVD_NAME:
            assert True
            return
    assert False

def test_rename():
    avd_to_rename = AVD.get_by_name(AVD_NAME)
    assert avd_to_rename is not None
    res = avd_to_rename.rename("new_test_avd")
    assert res is True
    assert avd_to_rename.name == "new_test_avd"
    hopefully_renamed_avd = AVD.get_by_name("new_test_avd")
    assert hopefully_renamed_avd is not None
    # Rename it back to the original
    res = hopefully_renamed_avd.rename(AVD_NAME)
    assert res is True

def test_delete_avd():
    # Get the avd and delete it
    avd_to_delete = AVD.get_by_name(AVD_NAME)
    assert avd_to_delete is not None
    avd_to_delete.delete()
    # Try to get it again and see if it exists
    hopefully_deleted_avd = AVD.get_by_name(AVD_NAME)
    assert hopefully_deleted_avd is None

