from gba import BIOS # type: ignore
from uctypes import addressof

CSET_DST_INC     = (0<<21)
CSET_DST_DEC	    = (1<<21)
CSET_DST_FIXED   = (2<<21)
CSET_DST_RELOAD  = (3<<21)

CSET_SRC_INC     = (0<<23)
CSET_SRC_DEC     = (1<<23)
CSET_SRC_FIXED   = (2<<23)

CSET_REPEAT      = (1<<25)

CSET_16          = (0<<26)
CSET_32          = (1<<26)

def vblank_intr_wait():
    BIOS.vblank_intr_wait()

def cpu_set_fast(source, destination, length_in_byte):
    """
        copy data fast, but the smallest block size is 32 bytes (8 words)
    """
    if not isinstance(source, int):
        source = addressof(source)
    if not isinstance(destination, int):
        destination = addressof(destination)
    repeat_count = length_in_byte // 4
    if repeat_count >= 2 ** 16:
        raise ValueError("data length is too long.")
    BIOS.cpu_set_fast(
        source,
        destination,
        CSET_32 | CSET_SRC_INC | CSET_DST_INC | repeat_count,
    )
