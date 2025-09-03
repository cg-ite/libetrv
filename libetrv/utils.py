from collections.abc import Iterable
from functools import wraps
from typing import Union, get_type_hints, TYPE_CHECKING, Awaitable, Callable

import xxtea
import asyncio

if TYPE_CHECKING:
    from .device import eTRVDevice


async def etrv_read_data(device: 'eTRVDevice', handlers, send_pin: bool, decode: bool) -> bytes:
    if not device.is_connected():
        await device.connect(send_pin)
    complete_data = bytearray()

    if not isinstance(handlers, Iterable):
        handlers = [handlers]

    for handler in handlers:
        # bleak expects UUID or handle as argument
        data = await device.client.read_gatt_char(handler)
        if decode:
            data = etrv_decode(data, device.secret)
        complete_data += data

    return bytes(complete_data)


async def etrv_write_data(device: 'eTRVDevice', handler, data: bytes, send_pin: bool, encode: bool):
    if encode:
        data = etrv_encode(data, device.secret)
    if not device.is_connected():
        await device.connect(send_pin)
    await device.client.write_gatt_char(handler, data, response=True)


def etrv_read(handlers: Union[int, Iterable], send_pin: bool = False, decode: bool = True):
    if not isinstance(handlers, Iterable):
        handlers = [handlers]
    def decorator(func: Callable) -> Callable[[object], Awaitable]:
        @wraps(func)
        async def wrapper(etrv):
            data = await etrv_read_data(etrv, handlers, send_pin, decode)
            hints = get_type_hints(func)
            cstruct_cls = hints.get('data')
            if cstruct_cls is not None:
                cstruct = cstruct_cls()
                cstruct.unpack(data)
                return await func(etrv, cstruct)
            return await func(etrv, data)
        return wrapper
    return decorator


def etrv_write(handler: int, send_pin: bool = False, encode: bool = True):
    def decorator(func: Callable) -> Callable[..., Awaitable]:
        @wraps(func)
        async def wrapper(etrv, *args):
            data = await func(etrv, *args)
            if hasattr(data, 'pack'):
                data = data.pack()
            await etrv_write_data(etrv, handler, data, send_pin, encode)
        return wrapper
    return decorator


def etrv_decode(data: bytes, key: bytes) -> bytes:
    data = etrv_reverse_chunks(data)
    data = xxtea.decrypt(bytes(data), key, padding=False)
    data = etrv_reverse_chunks(data)
    return data


def etrv_encode(data: bytes, key: bytes) -> bytes:
    data = etrv_reverse_chunks(data)
    data = xxtea.encrypt(bytes(data), key, padding=False)
    data = etrv_reverse_chunks(data)
    return data


def etrv_reverse_chunks(data: bytes):
    result = bytearray()
    for i in range(0, len(data), 4):
        result += data[i:i+4][::-1]
    return result
