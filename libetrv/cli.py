import asyncio
import time
import fire
from libetrv.device import eTRVDevice


def time_to_str(datetime):
    if datetime is not None:
        return datetime.strftime('%Y-%m-%d %H:%M:%S %Z')
    return None


class CLI:
    def __init__(self, pin=None, secret=None):
        self._pin = pin
        if secret is not None:
            self._secret = bytes.fromhex(secret)
        else:
            self._secret = None

    async def scan(self, timeout=10.0):
        print("Detected eTRV devices:")
        async for device, key in eTRVDevice.scan(timeout):
            key_str = key.hex() if key else "-"
            print("{}, RSSI={}dB, key={}".format(device.address, device.rssi, key_str))

    def device(self, device_id):
        return Device(device_id, self._pin, self._secret)


class Device:
    def __init__(self, device, pin, secret):
        self._pin = pin
        self._secret = secret
        self._device = eTRVDevice(device, pin=self._pin, secret=self._secret)

    async def get_handler(self, uuid):
        await self._device.connect(False)
        services = await self._device.client.get_services()
        for service in services:
            for char in service.characteristics:
                if str(char.uuid).lower() == str(uuid).lower():
                    print("Handler: 0x{:02X}".format(char.handle))
                    return
        print("UUID not found.")

    async def retrieve_key(self):
        print(
            "In 5 seconds this script will try to retrieve a secure key from eTRV device. "
            "Don't forget to save it for later. Before that be sure that device is in pairing mode. "
            "You can achieve that by pressing button on device"
        )
        await asyncio.sleep(5)
        secret = await self._device.secret_key()
        print("Secret Key:", secret.hex())

    def battery(self):
        result = self._device.battery
        print("Battery level: {}%".format(result))

    def pin_settings(self):
        result = self._device.pin_settings
        print('Pin number:  {:04d}'.format(result.pin_number))
        print('Pin enabled: {}'.format(result.pin_enabled))

    def settings(self):
        result = self._device.settings
        print('Frost protection temperature: {:.1f}°C'.format(result.frost_protection_temperature))
        print('Schedule mode:                {}'.format(result.schedule_mode))
        print('Vacation temperature:         {:.1f}°C'.format(result.vacation_temperature))
        print('Vacation From:                {}'.format(time_to_str(result.vacation_from)))
        print('Vacation To:                  {}'.format(time_to_str(result.vacation_to)))

    def temperature(self):
        temp = self._device.temperature
        print("Current room temperature: {:.1f}°C".format(temp.room_temperature))
        print("Set point temperature:    {:.1f}°C".format(temp.set_point_temperature))

    def name(self):
        device_name = self._device.name
        print("Device name: '{}'".format(device_name))

    def current_time(self):
        time_utc = self._device.current_time
        print("Current time: {}".format(time_to_str(time_utc)))

    def set_setpoint(self, setpoint: float):
        temp = self._device.temperature
        temp.set_point_temperature = setpoint
        temp.save()

    def set_pin(self, pin: int):
        settings = self._device.pin_settings
        if pin == 0:
            settings.pin_number = 0
            settings.pin_enabled = False
        elif 0 < pin <= 9999:
            settings.pin_number = pin
            settings.pin_enabled = True
        else:
            print('Invalid pin number')
            return
        settings.save()


if __name__ == "__main__":
    fire.Fire(CLI)
