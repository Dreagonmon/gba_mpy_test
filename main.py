print("==== main ====")
import gba # type: ignore
import gc
import utime

def free():
    start: int = utime.ticks_ms()
    gc.collect()
    mem = gc.mem_free()
    end: int = utime.ticks_ms()
    print(mem, utime.ticks_diff(end, start))

import gba_video
import gba_keypad
import gba_reg
import gba_bios

gba_video.map_background_palette_color_8bpp(0, gba_video.color555(255, 255, 255))
gba_video.map_background_palette_color_8bpp(1, gba_video.color555(0, 0, 0))

disp = gba_video.DispalyMode1()
bg_tile_block = gba_video.TileManager(0)
tile_image = gba_video.Tile(17, 1)
bg_map = gba_video.BGMap(16, 64, 64, True, True)
# bg_map = gba_video.BGMap(16, 64, 64, False, True)
bg0 = gba_video.BG0
bg2 = gba_video.BG2
disp.init_display()
disp.set_blank_display(True)
disp.apply()
tile_image.text(" 0123456789ABCDEF", 0, 0, 1)
bg_tile_block.set_tile_data(tile_image, 0)
bg_tile_block.update_all()
bg_map.set_bg_tile_at(1, 1, 5)
bg_map.set_bg_tile_at(2, 2, 4)
bg_map.set_bg_tile_at(3, 3, 3)
bg_map.set_bg_tile_at(4, 4, 2)
bg_map.set_bg_tile_at(5, 5, 1)
bg_map.update_all()
bg0.reset()
bg0.set_cbb(bg_tile_block.char_block)
bg0.set_color_mode(1)
bg0.set_sbb(bg_map.screen_block)
bg0.set_size(3) # 64x64
bg0.apply()
# bg2.reset()
# bg2.set_cbb(bg_tile_block.char_block)
# bg2.set_color_mode(1)
# bg2.set_sbb(bg_map.screen_block)
# bg2.set_size(2) # 64x64
# bg2.apply()
disp.enable_bg0(True)
# disp.enable_bg2(True)
disp.set_blank_display(False)
disp.apply()
gba_reg.REG_BG0OFS.HOFS = 4
gba_reg.REG_BG0OFS.VOFS = 4
gba_reg.REG_BG0OFS.apply()
# gba_reg.REG_BG2OFS.HOFS = 4
# gba_reg.REG_BG2OFS.VOFS = 4
# gba_reg.REG_BG2OFS.apply()
free()

import urandom
while True:
    start: int = utime.ticks_ms()
    bg_map.set_bg_tile_at(1, 1, urandom.randint(1, 16))
    bg_map.set_bg_tile_at(2, 2, urandom.randint(1, 16))
    bg_map.set_bg_tile_at(3, 3, urandom.randint(1, 16))
    bg_map.set_bg_tile_at(4, 4, urandom.randint(1, 16))
    bg_map.set_bg_tile_at(5, 5, urandom.randint(1, 16))
    end: int = utime.ticks_ms()
    print("Loop time:", utime.ticks_diff(end, start), "ms")
    # print(gc.mem_free())
    gba_bios.vblank_intr_wait()
    bg_map.update_all()

# disp = gba_video.DisplayMode4()
# disp.init_display()
# disp.text("Hello World", 16, 16, 1)
# disp.show()
# # loop
# col = 0
# color = 1
# end = utime.ticks_ms()
# last_key_event = 0
# while True:
#     start = end
#     # process event
#     while True:
#         event = gba_keypad.query_key_event()
#         if event & gba_keypad.EVENT_KEYDOWN:
#             print("key_down:", gba_keypad.key_mask_to_name(event & gba_keypad.KEY_MASK_ALL))
#         if event & gba_keypad.EVENT_KEYUP:
#             print("key_up:", gba_keypad.key_mask_to_name(event & gba_keypad.KEY_MASK_ALL))
#         if event & gba_keypad.EVENT_NONE:
#             break
#         last_key_event = event
#     # draw
#     disp.fill(0 if color else 1)
#     if not (last_key_event & gba_keypad.EVENT_NONE):
#         if last_key_event & gba_keypad.EVENT_KEYDOWN:
#             disp.text("KEY DOWN", 16, 16, color)
#         elif last_key_event & gba_keypad.EVENT_KEYUP:
#             disp.text("KEY UP", 16, 16, color)
#         name = gba_keypad.key_mask_to_name(last_key_event & gba_keypad.KEY_MASK_ALL)
#         disp.text(name, 96, 16, color)
#     disp.vline(col, 0, 160, color)
#     col += 1
#     if col >= 240:
#         col = 0
#         color = 0 if color else 1
#     disp.show()
#     end: int = utime.ticks_ms()
#     if not gba_keypad.get_key_status():
#         gba_keypad.set_query_status(gba_keypad.KEY_MASK_ALL, False)
#         gba_keypad.wait_until_keydown(gba_keypad.KEY_MASK_ALL)
    # print("full screen refresh time:", end=" ")
    # print(utime.ticks_diff(end, start), end="ms\n")
    # free()
    # gc.collect()
