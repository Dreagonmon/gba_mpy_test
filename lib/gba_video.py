from machine import mem16
from framebuf import FrameBuffer, GS8
from gba_bios import vblank_intr_wait, cpu_set_fast
from gba_reg import IndirectVisitedRegister, REG_DISPCNT, REG_BG0CNT
from gba_reg import REG_BG0CNT, REG_BG1CNT, REG_BG2CNT, REG_BG3CNT

REG_BG_PALETTE = 0x05000000  # u16
REG_SPRITE_PALETTE = 0x05000200  # u16
MODE_1 = 1  # BG Mode 1, 2 text background, 1 Rotate Background
MODE_4 = 4  # BG Mode 4, 8bit Paletted Bitmap
MASK_BUF_PAGE = (0b1 << 4)
BG0_ON = (0b1 << 8)
BG1_ON = (0b1 << 9)
BG2_ON = (0b1 << 10)
BG3_ON = (0b1 << 11)
FRAMEBUF0_ADDR = 0x06000000
FRAMEBUF1_ADDR = 0x0600A000
BG_TILE_ADDR = 0x06000000
SPRITE_TILE_ADDR = 0x06010000
BG_MAP_ADDR = 0x06000000

# tile copy buffer
tmp_buffer = bytearray(8 * 8)
tmp_frame = FrameBuffer(tmp_buffer, 8, 8, GS8)


def color555(r, g, b):
    return ((r >> 3) & 0b11111) | (((g >> 3) & 0b11111) << 5) | (((b >> 3) & 0b11111) << 10)


def map_background_palette_color_8bpp(palette_index: int, color555: int):
    if palette_index < 0 or palette_index >= 256:
        return
    mem16[REG_BG_PALETTE + (2 * palette_index)] = color555 & 0xFFFF


def map_sprite_palette_color_8bpp(palette_index: int, color555: int):
    if palette_index < 0 or palette_index >= 256:
        return
    mem16[SPRITE_TILE_ADDR + (2 * palette_index)] = color555 & 0xFFFF

# all tiles are d-tiles, 8bit palette, to make things simple


class Tile(FrameBuffer):
    def __init__(self, tile_w: int, tile_h: int):
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.buffer = bytearray(tile_w * 8 * tile_h * 8)
        super().__init__(self.buffer, tile_w * 8, tile_h * 8, GS8)

    @property
    def tile_size(self):
        return self.tile_w * self.tile_h


class TileManager():
    """ A charblock of tiles, 256 8bpp tiles"""

    def __init__(self, char_block: int, create_buffer: bool = True):
        """ 0-3 is bg tiles, 4-5 is sprite tiles """
        if char_block < 0 or char_block >= 6:
            raise ValueError()
        self.char_block = char_block
        self.buffer = bytearray(256 * 8 * 8) if create_buffer else bytearray()

    def __len__(self):
        return len(self.buffer)

    def update_all(self):
        cpu_set_fast(self.buffer, self.char_block * 256 *
                     8 * 8 + BG_TILE_ADDR, len(self.buffer))

    def set_tile_data(self, tile: Tile, tile_offset: int):
        for y in range(tile.tile_h):
            for x in range(tile.tile_w):
                # clip the image
                tmp_frame.blit(tile, -(x * 8), -(y * 8))
                offset = tile_offset + y * tile.tile_w + x
                offset *= 8*8
                self.buffer[offset: offset+8*8] = tmp_buffer


class BGMap():
    """ background map, align to screenblock """

    def __init__(self, screen_block: int, tile_w: int, tile_h: int, is_regular_bg: bool, create_buffer: bool = True):
        if screen_block < 0 or screen_block >= 32:
            raise ValueError()
        self.tile_w = tile_w
        self.tile_h = tile_h
        self.screen_block = screen_block
        self.byte_per_entry = 2 if is_regular_bg else 1
        self.buffer = bytearray(
            tile_w * tile_h * self.byte_per_entry) if create_buffer else bytearray()

    def __len__(self):
        return len(self.buffer)

    def update_all(self):
        cpu_set_fast(self.buffer, self.screen_block * 32 *
                     8 * 8 + BG_MAP_ADDR, len(self.buffer))

    def set_regular_bg_tile_at(self, tile_x: int, tile_y: int, tile_index: int, h_flip=False, v_flip=False, palette_bank=0, apply_now=False):
        # calc index
        buf = self.buffer
        n = tile_y * 32 + tile_x
        if tile_x >= 32:
            n += 0x03E0
        if tile_y >= 32 and self.tile_w >= 64:
            n += 0x0400
        tile_data = tile_index
        tile_data |= (1 << 10) if h_flip else 0
        tile_data |= (1 << 11) if v_flip else 0
        tile_data |= (palette_bank & 0b1111) << 12
        if buf:
            buf[n * 2] = tile_data & 0xFF
            buf[n * 2 + 1] = (tile_data >> 8) & 0xFF
        if apply_now:
            _off = self.screen_block * 32 * 8 * 8 + BG_MAP_ADDR
            _off += n * 2
            mem16[_off] = tile_data

    def set_affine_bg_tile_at(self, tile_x: int, tile_y: int, tile_index: int, apply_now=False):
        # calc index
        buf = self.buffer
        n = self.tile_w * tile_y + tile_x
        buf[n] = tile_index & 0xFF
        if apply_now:
            n -= (n % 2)
            _off = self.screen_block * 32 * 8 * 8 + BG_MAP_ADDR
            _off += n
            mem16[_off] = (buf[n]) | (buf[n+1] << 8)
    
    def set_bg_tile_at(self, tile_x: int, tile_y: int, tile_index: int, h_flip=False, v_flip=False, palette_bank=0, apply_now=False):
        if self.byte_per_entry == 2:
            self.set_regular_bg_tile_at(
                tile_x, tile_y, tile_index,
                h_flip, v_flip, palette_bank,
                apply_now
            )
        else:
            self.set_affine_bg_tile_at(tile_x, tile_y, tile_index, apply_now)
    


class Background():
    def __init__(self, bgcnt: IndirectVisitedRegister):
        self._bgcnt = bgcnt
        self.reset = bgcnt.reset
        self.apply = bgcnt.write_by_halfword

    def set_priority(self, prio: int):
        """ drawing order of backgrounds. Values: 0-3 """
        self._bgcnt.PRIO = prio & 0b11

    def set_cbb(self, cbb: int):
        """ Charblock that serves as the base for character/tile indexing. Values: 0-3 """
        self._bgcnt.CBB = cbb & 0b11

    def set_mosaic(self, mosaic: bool):
        """ Enables mosaic effect """
        self._bgcnt.MOSAIC = 1 if mosaic else 0

    def set_color_mode(self, color_mode: int):
        """ Color Mode, 0: 16 colors, 1: 256 colors """
        self._bgcnt.CM = color_mode & 0b1

    def set_sbb(self, sbb: int):
        """ Screenblock that serves as the base for screen-entry/map indexing. Values: 0-31 """
        self._bgcnt.SBB = sbb & 0b11111

    def set_wrap(self, wrap: bool):
        """ Enables mosaic effect """
        self._bgcnt.WRAP = 1 if wrap else 0

    def set_size(self, size: int) -> int:
        """ Background Size, Regular and affine backgrounds have different sizes available to them

        * Regular bg sizes 
        | Sz-flag  | define       | (tiles) | (pixels) |
        |:--------:|:------------:|:-------:|:--------:|
        | 0b00 (0) | BG_REG_32x32 | 32×32   | 256×256  |
        | 0b01 (1) | BG_REG_64x32 | 64×32   | 512×256  |
        | 0b10 (2) | BG_REG_32x64 | 32×64   | 256×512  |
        | 0b11 (3) | BG_REG_64x64 | 64×64   | 512×512  |

        * Affine bg sizes
        | Sz-flag  | define         | (tiles) | (pixels)  |
        |:--------:|:--------------:|:-------:|:---------:|
        | 0b00 (0) | BG_AFF_16x16   | 16×16   | 128×128   |
        | 0b01 (1) | BG_AFF_32x32   | 32×32   | 256×256   |
        | 0b10 (2) | BG_AFF_64x64   | 64×64   | 512×512   |
        | 0b11 (3) | BG_AFF_128x128 | 128×128 | 1024×1024 |
        """
        self._bgcnt.SIZE = size & 0b11


class Display():
    def __init__(self):
        self.reset = REG_DISPCNT.reset
        self.apply = REG_DISPCNT.write_by_halfword

    def enable_bg0(self, status: bool):
        REG_DISPCNT.BG0 = 1 if status else 0

    def enable_bg1(self, status: bool):
        REG_DISPCNT.BG1 = 1 if status else 0

    def enable_bg2(self, status: bool):
        REG_DISPCNT.BG2 = 1 if status else 0

    def enable_bg3(self, status: bool):
        REG_DISPCNT.BG3 = 1 if status else 0

    def set_blank_display(self, blank: bool):
        REG_DISPCNT.BLANK = 1 if blank else 0


class DispalyMode1(Display):
    # display mode with 2 text background and 1 rotate background
    def __init__(self):
        super().__init__()

    def init_display(self):
        self.reset()
        # set mode 1
        REG_DISPCNT.reset()
        REG_DISPCNT.MODE = MODE_1
        REG_DISPCNT.write_by_halfword()


class DisplayMode4(FrameBuffer):
    def __init__(self):
        self.buffer = bytearray(240*160)
        self.current_page = 0
        super(FrameBuffer).__init__(self.buffer, 240, 160, GS8)

    def init_display(self):
        # set mode 4 (8bit paletted bitmapped mode), enable bg2
        self.current_page = 0
        REG_DISPCNT.PAGE = 0
        REG_DISPCNT.MODE = MODE_4
        REG_DISPCNT.BG2 = 1
        REG_DISPCNT.write_by_halfword()

    def show(self):
        # check page
        self.current_page = REG_DISPCNT.PAGE
        # write data
        cpu_set_fast(
            self.buffer, FRAMEBUF0_ADDR if self.current_page else FRAMEBUF1_ADDR, 240*160)
        vblank_intr_wait()
        if self.current_page:
            REG_DISPCNT.PAGE = 0
        else:
            REG_DISPCNT.PAGE = 1
        REG_DISPCNT.write_by_halfword()


BG0 = Background(REG_BG0CNT)
BG1 = Background(REG_BG1CNT)
BG2 = Background(REG_BG2CNT)
BG3 = Background(REG_BG3CNT)
