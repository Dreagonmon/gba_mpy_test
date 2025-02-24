from machine import mem16
from gba import BIOS # type: ignore

REG_KEYINPUT        = 0x04000130 # u16
REG_KEYCNT          = 0x04000132 # u16

IRQ_KEYPAD          = (1<<12)

KEY_A               = (1 << 0)
KEY_B               = (1 << 1)
KEY_SELECT          = (1 << 2)
KEY_START           = (1 << 3)
KEY_RIGHT           = (1 << 4)
KEY_LEFT            = (1 << 5)
KEY_UP              = (1 << 6)
KEY_DOWN            = (1 << 7)
KEY_R               = (1 << 8)
KEY_L               = (1 << 9)
KEY_MASK_ALL        = 0b0000_0011_1111_1111

EVENT_KEYDOWN       = (0b0001 << 16)
EVENT_KEYUP         = (0b0010 << 16)
EVENT_NONE          = (0b1000 << 16)

KEY_MASK_NAME_MAP = {
    KEY_A: "A",
    KEY_B: "B",
    KEY_SELECT: "SELECT",
    KEY_START: "START",
    KEY_RIGHT: "RIGHT",
    KEY_LEFT: "LEFT",
    KEY_UP: "UP",
    KEY_DOWN: "DOWN",
    KEY_R: "R",
    KEY_L: "L",
}

last_status = 0b0000_0000_0000_0000 # default all key up

def is_keydown(key_mask: int) -> bool:
    # print(bin(mem16[REG_KEYINPUT] | 0b10000000_00000000))
    return ((~mem16[REG_KEYINPUT]) & key_mask & KEY_MASK_ALL) > 0

def get_key_status() -> int:
    return ~(mem16[REG_KEYINPUT]) & KEY_MASK_ALL

def query_key_event() -> int:
    global last_status
    current: int = ~(mem16[REG_KEYINPUT]) & KEY_MASK_ALL
    for bit in range(10):
        key_mask = 1 << bit
        if (current & key_mask) > 0 and (last_status & key_mask) == 0:
            # key down
            last_status = last_status | key_mask
            return EVENT_KEYDOWN | key_mask
        elif (current & key_mask) == 0 and (last_status & key_mask) > 0:
            # key up
            last_status = last_status & (~key_mask)
            return EVENT_KEYUP | key_mask
    return EVENT_NONE | current

def set_query_status(key_mask: int, set_key_down = False):
    global last_status
    if set_key_down:
        last_status = last_status | key_mask
    else:
        last_status = last_status & (~key_mask)

def key_mask_to_name(key_mask: int) -> str:
    if key_mask in KEY_MASK_NAME_MAP:
        return KEY_MASK_NAME_MAP[key_mask]
    return ""

def wait_until_keydown(key_mask: int, when_any = True) -> bool:
    key_mask = key_mask & KEY_MASK_ALL
    key_mask = key_mask | (1 << 14)
    key_mask = key_mask | ((0 if when_any else 1) << 15)
    mem16[REG_KEYCNT] = key_mask
    BIOS.intr_wait(0, IRQ_KEYPAD)
