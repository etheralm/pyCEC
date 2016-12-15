import asyncio
from unittest import TestCase

import time

from pycec.const import CMD_POWER_STATUS, CMD_OSD_NAME, CMD_VENDOR, CMD_PHYSICAL_ADDRESS
from pycec.datastruct import CecCommand
from pycec.network import HdmiNetwork, HdmiDevice


def clear_event_loop():
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        loop = asyncio.new_event_loop()
    loop.stop()
    loop.run_forever()


class TestHdmiNetwork(TestCase):
    pass

    def test_scan(self):
        network = HdmiNetwork(MockConfig(), MockAdapter(
            [True, True, False, True, False, True, False, False, False, False, False, False, False, False, False,
             False]), scan_interval=0)
        network._scan_delay = 0
        #network.scan()
        #clear_event_loop()
        loop=asyncio.new_event_loop()
        loop.run_in_executor(None, network.scan)
        time.sleep(1)
        loop.stop()
        loop.run_forever()
        #loop.run_until_complete(network.scan())
        self.assertIn(HdmiDevice(0), network.devices)
        device = network.get_device(0)
        self.assertEqual(device.osd_name, '')
        device.request_name()
        self.assertEqual(device.osd_name, "Test")
        self.assertEqual(device.power_status, 0)
        device.request_power_status()
        self.assertEqual(device.power_status, 2)
        for d in network.devices:
            d.stop()

    def test_devices(self):
        network = HdmiNetwork(MockConfig(), MockAdapter(
            [True, True, False, True, False, True, False, False, False, False, False, False, False, False, False,
             False]), scan_interval=0)
        network._scan_delay = 0
        network.scan()
        clear_event_loop()
        for i in [0, 1, 3, 5]:
            self.assertIn(HdmiDevice(i), network.devices)
        for i in [2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
            self.assertNotIn(HdmiDevice(i), network.devices)
        for d in network.devices:
            d.stop()

    def tearDown(self):
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.run_forever()


class MockConfig:
    def __init__(self):
        self._command_callback = None

    def SetCommandCallback(self, callback):
        self._command_callback = callback

    def GetCommandCallback(self):
        return self._command_callback


class LogicalAddress:
    def __init__(self, i):
        self.primary = i


class MockAdapter:
    def __init__(self, data):
        self._data = data
        self._config = MockConfig()

    def PollDevice(self, i):
        return self._data[i]

    def Transmit(self, command):
        response = CecCommand(src=command.dst, dst=command.src)
        if command.cmd == CMD_POWER_STATUS[0]:
            response.cmd = CMD_POWER_STATUS[1]
            response.att = [2]
            self._config.GetCommandCallback()(response.raw)
        elif command.cmd == CMD_OSD_NAME[0]:
            response.cmd = CMD_OSD_NAME[1]
            response.att = (ord(i) for i in "Test")
            self._config.GetCommandCallback()(response.raw)
        elif command.cmd == CMD_VENDOR[0]:
            response.cmd = CMD_VENDOR[1]
            response.att = [0x00, 0x09, 0xB0]
            self._config.GetCommandCallback()(response.raw)
        elif command.cmd == CMD_PHYSICAL_ADDRESS[0]:
            response.cmd = CMD_PHYSICAL_ADDRESS[1]
            response.att = [0x09, 0xB0]
            self._config.GetCommandCallback()(response.raw)

    def CommandFromString(self, cmd: str) -> CecCommand:
        return CecCommand(cmd)

    def GetLogicalAddresses(self):
        return LogicalAddress(2)

    def GetCurrentConfiguration(self):
        return self._config

    def SetConfiguration(self, config):
        self._config = config
