import asyncio
from bleak import BleakClient, BleakScanner
from loguru import logger

from .data_struct import BatteryData, PinSettingsData, SettingsData, TemperatureData, CurrentTimeData, SecretKeyData, NameData
from .properties import eTRVProperty
from .utils import etrv_read, etrv_write

class eTRVDeviceMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super(eTRVDeviceMeta, mcls).__new__(mcls, name, bases, attrs)
        for attr, obj in attrs.items():
            if isinstance(obj, eTRVProperty):
                obj.__set_name__(cls, attr)
        return cls

class eTRVDevice(metaclass=eTRVDeviceMeta):
    def __init__(self, address, secret=None, pin=None, retry_limit=None):
        self.address = address
        self.secret = secret
        self.pin = b'\0\0\0\0' if pin is None else pin.to_bytes(4, byteorder='big')
        self.client = None
        self.__pin_already_sent = False
        self.fields = {}
        self.retry_limit = retry_limit

    @staticmethod
    async def scan(timeout=10.0, n_expected=1000):
        seen = set()
        n = 0
        for _ in range(int(timeout)):
            devices = await BleakScanner.discover(timeout=2.0)
            for d in devices:
                if d.address in seen:
                    continue

                seen.add(d.address)

                # Hier kannst du die Logik anpassen, um die gewünschten Geräte zu identifizieren
                if d.name and d.name.endswith(';eTRV'):
                    n += 1
                    eTRV = eTRVDevice(d.address)
                    await eTRV.connect()
                    secret_key = eTRV.secret_key
                    await eTRV.disconnect()
                    yield d, secret_key

                if n == n_expected:
                    break

    def is_connected(self):
        return self.client and self.client.is_connected

    async def connect(self, send_pin: bool = False):
        logger.debug("Trying to connect to {}", self.address)
        if self.is_connected():
            logger.debug("Device already connected {}", self.address)
            return

        retry_limit = self.retry_limit

        while retry_limit is None or retry_limit >= 0:
            try:
                self.client = BleakClient(self.address)
                logger.debug("Trying to connect to Device {}", self.address)
                await self.client.connect()
                if send_pin:
                    await self.send_pin()
                break
            except Exception as e:
                logger.error("Unable to connect to {}. Retrying in 100ms. Error: {}", self.address, e)
                if retry_limit is not None:
                    retry_limit -= 1
                    if retry_limit < 0:
                        raise
                await asyncio.sleep(0.1)

    async def disconnect(self):
        logger.debug("Disconnecting")
        if self.client:
            await self.client.disconnect()
            self.client = None
            self.__pin_already_sent = False
            for field in self.fields.values():
                field.invalidate()

    async def send_pin(self):
        if not self.__pin_already_sent:
            logger.debug("Writing PIN to {}", self.address)
            pin_handler_uuid = "10020001-2749-0001-0000-00805f9b34fb" #"00000x24-0000-1000-8000-00805f9b34fb"  # Ersetze durch die tatsächliche UUID
            await self.client.write_gatt_char(pin_handler_uuid, self.pin, response=True)
            self.__pin_already_sent = True

    battery = eTRVProperty(BatteryData)
    pin_settings = eTRVProperty(PinSettingsData)
    settings = eTRVProperty(SettingsData)
    temperature = eTRVProperty(TemperatureData)
    name = eTRVProperty(NameData)
    current_time = eTRVProperty(CurrentTimeData)
    secret_key = eTRVProperty(SecretKeyData)
