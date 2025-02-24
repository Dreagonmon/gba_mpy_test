from machine import mem32
from uctypes import addressof
from gba import BIOS # type: ignore

REG_DMA0SAD     = 0x040000b0
REG_DMA0DAD     = 0x040000b4
REG_DMA0CNT     = 0x040000b8

REG_DMA1SAD     = 0x040000bc
REG_DMA1DAD     = 0x040000c0
REG_DMA1CNT     = 0x040000c4

REG_DMA2SAD     = 0x040000c8
REG_DMA2DAD     = 0x040000cc
REG_DMA2CNT     = 0x040000d0

REG_DMA3SAD     = 0x040000d4
REG_DMA3DAD     = 0x040000d8
REG_DMA3CNT     = 0x040000dc

DMA_DST_INC     = (0<<21)
DMA_DST_DEC	    = (1<<21)
DMA_DST_FIXED   = (2<<21)
DMA_DST_RELOAD  = (3<<21)

DMA_SRC_INC     = (0<<23)
DMA_SRC_DEC     = (1<<23)
DMA_SRC_FIXED   = (2<<23)

DMA_REPEAT      = (1<<25)

DMA16           = (0<<26)
DMA32           = (1<<26)

DMA_IMMEDIATE   = (0<<28)
DMA_VBLANK      = (1<<28)
DMA_HBLANK      = (2<<28)
DMA_SPECIAL     = (3<<28)

DMA_IRQ	        = (1<<30)
DMA_ENABLE      = (1<<31)

IRQ_DMA0        = (1<<8)
IRQ_DMA1        = (1<<9)
IRQ_DMA2        = (1<<10)
IRQ_DMA3        = (1<<11)

def dma3_copy_by_word(source, destination, length_in_byte):
    if not isinstance(source, int):
        source = addressof(source)
    if not isinstance(destination, int):
        destination = addressof(destination)
    repeat_count = length_in_byte // 4
    if length_in_byte // 4 >= 2 ** 16:
        raise ValueError("DMA length is too long.")
    mem32[REG_DMA3SAD] = source
    mem32[REG_DMA3DAD] = destination
    mem32[REG_DMA3CNT] = repeat_count | DMA_DST_INC | DMA_SRC_INC | DMA32 | DMA_IMMEDIATE | DMA_ENABLE
    # When you activate DMA the so-called DMA controller takes over the hardware
    # (the CPU is actually halted)
    # so there is no need to wait, function will return once the operation end.
