import uctypes as ut
from machine import mem16, mem32


class IndirectVisitedRegister():
    def __init__(self, addr: int, layout: dict, layout_type: int = ut.NATIVE, is_32bit: bool = False):
        # by pass modified version of __setattr__
        super().__setattr__("_is_32bit", is_32bit)
        super().__setattr__("_addr", addr)
        super().__setattr__("_buf", bytearray(ut.sizeof(layout, layout_type)))
        super().__setattr__("_reg", ut.struct(ut.addressof(self._buf), layout, layout_type))

    def __TYPING_HINT__(self):
        self._is_32bit: bool
        self._addr: int
        self._buf: bytearray
        self._reg: any

    def __getattr__(self, name):
        return getattr(self._reg, name)

    def __setattr__(self, name, value):
        return setattr(self._reg, name, value)

    def write_by_halfword(self):
        for offset in range(len(self._buf)):
            if offset % 2:
                continue
            # print("Writing halfword to:", hex(self._addr + offset), bin((self._buf[offset]) | (self._buf[offset + 1] << 8) | 0b1_0000_0000_0000_0000))
            mem16[
                self._addr + offset
            ] = (self._buf[offset]) | (self._buf[offset + 1] << 8)

    def write_by_word(self):
        for offset in range(len(self._buf)):
            if offset % 4:
                continue
            # print("Writing word to:", hex(self._addr + offset))
            mem32[self._addr + offset] = (
                (self._buf[offset])
                | (self._buf[offset + 1] << 8)
                | (self._buf[offset + 2] << 16)
                | (self._buf[offset + 3] << 24)
            )

    def read_by_halfword(self):
        for offset in range(len(self._buf)):
            if offset % 2:
                continue
            val = mem16[self._addr + offset]
            self._buf[offset] = val & 0xFF
            self._buf[offset + 1] = (val >> 8) & 0xFF

    def read_by_word(self):
        for offset in range(len(self._buf)):
            if offset % 4:
                continue
            val = mem32[self._addr + offset]
            self._buf[offset] = val & 0xFF
            self._buf[offset + 1] = (val >> 8) & 0xFF
            self._buf[offset + 2] = (val >> 16) & 0xFF
            self._buf[offset + 3] = (val >> 24) & 0xFF

    def apply(self):
        if self._is_32bit:
            self.write_by_word()
        else:
            self.write_by_halfword()

    def load(self):
        if self._is_32bit:
            self.read_by_word()
        else:
            self.read_by_halfword()

    def reset(self):
        for i in range(len(self._buf)):
            self._buf[i] = 0x00


REG_DISPCNT_LAYOUT = {
    # Sets video mode. 0, 1, 2 are tiled modes; 3, 4, 5 are bitmap modes.
    "MODE": (0 | ut.BFUINT16 | 0 << ut.BF_POS | 3 << ut.BF_LEN),
    # Is set if cartridge is a GBC game. Read-only.
    "GB_MODE": (0 | ut.BFUINT16 | 3 << ut.BF_POS | 1 << ut.BF_LEN),
    # Page select. Modes 4 and 5 can use page flipping for smoother animation.
    # This bit selects the displayed page (and allowing the other one to be drawn on without artifacts).
    "PAGE": (0 | ut.BFUINT16 | 4 << ut.BF_POS | 1 << ut.BF_LEN),
    # Allows access to OAM in an HBlank. OAM is normally locked in VDraw.
    # Will reduce the amount of sprite pixels rendered per line.
    "OAM_HBL": (0 | ut.BFUINT16 | 5 << ut.BF_POS | 1 << ut.BF_LEN),
    # Object mapping mode.
    # Tile memory can be seen as a 32x32 matrix of tiles.
    # When sprites are composed of multiple tiles high, this bit tells whether the next row of tiles lies beneath the previous,
    # in correspondence with the matrix structure (2D mapping, OM=0), or right next to it,
    # so that memory is arranged as an array of sprites (1D mapping OM=1). More on this in the sprite chapter.
    "OBJ_1D": (0 | ut.BFUINT16 | 6 << ut.BF_POS | 1 << ut.BF_LEN),
    # Force a screen blank.
    "BLANK": (0 | ut.BFUINT16 | 7 << ut.BF_POS | 1 << ut.BF_LEN),
    # Enables rendering of the corresponding background and sprites.
    "BG0": (0 | ut.BFUINT16 | 8 << ut.BF_POS | 1 << ut.BF_LEN),
    "BG1": (0 | ut.BFUINT16 | 9 << ut.BF_POS | 1 << ut.BF_LEN),
    "BG2": (0 | ut.BFUINT16 | 10 << ut.BF_POS | 1 << ut.BF_LEN),
    "BG3": (0 | ut.BFUINT16 | 11 << ut.BF_POS | 1 << ut.BF_LEN),
    "OBJ": (0 | ut.BFUINT16 | 12 << ut.BF_POS | 1 << ut.BF_LEN),
    # Enables the use of windows 0, 1 and Object window, respectively.
    # Windows can be used to mask out certain areas (like the lamp did in Zelda:LTTP).
    "WIN0": (0 | ut.BFUINT16 | 13 << ut.BF_POS | 1 << ut.BF_LEN),
    "WIN1": (0 | ut.BFUINT16 | 14 << ut.BF_POS | 1 << ut.BF_LEN),
    "WINOBJ": (0 | ut.BFUINT16 | 15 << ut.BF_POS | 1 << ut.BF_LEN),
}
REG_DISPCNT = IndirectVisitedRegister(
    0x04000000, REG_DISPCNT_LAYOUT, ut.NATIVE, False)

"""
Table 9.4a: regular bg sizes 
Sz-flag  define        (tiles) (pixels)
00       BG_REG_32x32  32×32   256×256
01       BG_REG_64x32  64×32   512×256
10       BG_REG_32x64  32×64   256×512
11       BG_REG_64x64  64×64   512×512
Table 9.4b: affine bg sizes
Sz-flag  define         (tiles)  (pixels)
00       BG_AFF_16x16   16×16    128×128
01       BG_AFF_32x32   32×32    256×256
10       BG_AFF_64x64   64×64    512×512
11       BG_AFF_128x128 128×128  1024×1024 
"""
REG_BGCNT_LAYOUT = {
    # Priority. Determines drawing order of backgrounds.
    "PRIO": (0 | ut.BFUINT16 | 0 << ut.BF_POS | 2 << ut.BF_LEN),
    # Character Base Block. Sets the charblock that serves as the base for character/tile indexing. Values: 0-3.
    "CBB": (0 | ut.BFUINT16 | 2 << ut.BF_POS | 2 << ut.BF_LEN),
    # Mosaic flag. Enables mosaic effect.
    "MOSAIC": (0 | ut.BFUINT16 | 6 << ut.BF_POS | 1 << ut.BF_LEN),
    # Color Mode. 16 colors (4bpp) if cleared; 256 colors (8bpp) if set.
    "CM": (0 | ut.BFUINT16 | 7 << ut.BF_POS | 1 << ut.BF_LEN),
    # Screen Base Block. Sets the screenblock that serves as the base for screen-entry/map indexing. Values: 0-31.
    "SBB": (0 | ut.BFUINT16 | 8 << ut.BF_POS | 5 << ut.BF_LEN),
    # Affine Wrapping flag. If set, affine background wrap around at their edges.
    # Has no effect on regular backgrounds as they wrap around by default.
    "WRAP": (0 | ut.BFUINT16 | 13 << ut.BF_POS | 1 << ut.BF_LEN),
    # Background Size. Regular and affine backgrounds have different sizes available to them.
    "SIZE": (0 | ut.BFUINT16 | 14 << ut.BF_POS | 2 << ut.BF_LEN),
}
REG_BG0CNT = IndirectVisitedRegister(
    0x04000008, REG_BGCNT_LAYOUT, ut.NATIVE, False)
REG_BG1CNT = IndirectVisitedRegister(
    0x0400000a, REG_BGCNT_LAYOUT, ut.NATIVE, False)
REG_BG2CNT = IndirectVisitedRegister(
    0x0400000c, REG_BGCNT_LAYOUT, ut.NATIVE, False)
REG_BG3CNT = IndirectVisitedRegister(
    0x0400000e, REG_BGCNT_LAYOUT, ut.NATIVE, False)

"""
Each background has two 16-bit scrolling registers to offset the rendering (REG_BGxHOFS and REG_BGxVOFS).
There are a number of interesting points about these.
First, because regular backgrounds wrap around, the values are essentially modulo mapsize.
This is not really relevant at the moment, but you can use this to your benefit once you get to more advanced tilemaps.
Second, these registers are write-only! It means that you can’t update the position by simply doing REG_BG0HOFS++ and the like.
"""
REG_BGOFS_LAYOUT = {
    "HOFS": (0x00 | ut.INT16),
    "VOFS": (0x02 | ut.INT16),
}
REG_BG0OFS = IndirectVisitedRegister(
    0x04000010, REG_BGOFS_LAYOUT, ut.NATIVE, False)
REG_BG1OFS = IndirectVisitedRegister(
    0x04000014, REG_BGOFS_LAYOUT, ut.NATIVE, False)
REG_BG2OFS = IndirectVisitedRegister(
    0x04000018, REG_BGOFS_LAYOUT, ut.NATIVE, False)
REG_BG3OFS = IndirectVisitedRegister(
    0x0400001c, REG_BGOFS_LAYOUT, ut.NATIVE, False)
