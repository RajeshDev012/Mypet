"""
Desktop Pixel Cat
Developed by RajeshDev012
https://github.com/RajeshDev012
-----------------
- Sits on top of all windows (transparent background, no title bar)
- Eyes follow your mouse cursor
- Pops up a keyboard and taps its paws when you type (any app)
- Drag with left mouse button, right-click for Quit

Install:  pip install pynput
Run:      python desktop_cat_version1.py
(Windows works best. On macOS, allow Accessibility/Input Monitoring for
Terminal/Python so key presses can be detected.)
"""
import random
import sys
import time
import tkinter as tk

from pynput import keyboard

SCALE = 5                 # pixel size on screen; make bigger for a bigger cat
TRANS = "#ff00ff"         # colour treated as transparent (Windows)
TYPING_TIMEOUT = 1.2      # seconds after last key before cat goes idle
SLEEP_AFTER = 10          # seconds without mouse/keyboard activity -> cat sleeps

KEY_FACE = "#9a9a9a"
KEY_BASE = "#554545"

# --- pixel art: '#' = black body. White outline is auto-generated. ---------
BODY_ROWS = [
    "..##........##",
    "..###......###",
    "..############",
    "..############",
    "..############",
    "..############",
    "..############",
    ".....######...",
    "....########..",
    "...##########.",
    "..############",
    ".##############.....##",
    ".##############....###",
    ".###############..##.#",
    ".###################.#",
    ".##############",
]
BODY = {(x, y) for y, row in enumerate(BODY_ROWS)
        for x, ch in enumerate(row) if ch == "#"}

# The body spans columns 1..14, so everything below is mirrored around x = 7.5
# Left paw 3-5  <->  right paw 10-12 ;  left key 1-7  <->  right key 8-14
PAW_X = (3, 10)
KEY_X = (1, 8)
PAW_W, KEY_W = 3, 7
KEY_TOP, KEY_BASE_ROW = 19, 21      # key face starts at row 19, base at row 21

LEFT_EYE = (4, 4)         # top-left cell of 2x2 eye
RIGHT_EYE = (10, 4)
WHISKERS = {(0, 4), (0, 6), (15, 4), (15, 6)}

# Sleeping cat: a lying "loaf" at the bottom of the same 24x24 grid
SLEEP_ROWS = [
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "..##........##........",
    "..###......###........",
    "..############........",
    "..############........",
    ".##################...",
    ".####################.",
    ".#####################",
    ".#####################",
]
SLEEP_BODY = {(x, y) for y, row in enumerate(SLEEP_ROWS)
              for x, ch in enumerate(row) if ch == "#"}
SLEEP_EYES = {(4, 11), (5, 11), (10, 11), (11, 11)}   # closed eyes (white lines)


def z_cells(x, y):
    return {(x, y), (x + 1, y), (x + 2, y), (x + 1, y + 1),
            (x, y + 2), (x + 1, y + 2), (x + 2, y + 2)}


GRID_W, GRID_H = 24, 24   # includes 1-cell margin for the outline
WIN_W, WIN_H = GRID_W * SCALE, GRID_H * SCALE


def finish(px, cells, extra_outline=()):
    """Add auto outline + body colours, return a zoomed PhotoImage."""
    outline = set()
    for (x, y) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in cells:
                    outline.add(n)
    outline |= set(extra_outline)
    for p in outline:
        px[p] = "white"
    for p in cells:
        px[p] = "black"
    return outline


def to_image(px):
    img = tk.PhotoImage(width=GRID_W, height=GRID_H)
    for (x, y), color in px.items():
        img.put(color, to=(x + 1, y + 1))
    return img.zoom(SCALE, SCALE)


def render_sleep(zphase):
    px = {}
    cells = set(SLEEP_BODY)
    cells |= z_cells(16, 5 - zphase) | z_cells(19, 1 - zphase)
    finish(px, cells)
    for p in SLEEP_EYES:
        px[p] = "white"
    return to_image(px)


def render(ox, oy, blink, typing, paw, sleeping=False, zphase=0):
    """Build one frame as a PhotoImage (one image = no flicker, no lag)."""
    if sleeping:
        return render_sleep(zphase)
    px = {}

    if typing:
        for i in range(2):
            pressed = (paw == i)
            top = KEY_TOP + (1 if pressed else 0)       # pressed key sinks 1 row
            for x in range(KEY_X[i], KEY_X[i] + KEY_W):
                for y in range(top, KEY_BASE_ROW):
                    px[(x, y)] = KEY_FACE
                px[(x, KEY_BASE_ROW)] = KEY_BASE

    cells = set(BODY)
    if typing:
        for i in range(2):
            pressed = (paw == i)
            # up: stops one row above the key; down: touches the pressed key
            bottom = (KEY_TOP + 1 - 1) if pressed else (KEY_TOP - 2)
            for x in range(PAW_X[i], PAW_X[i] + PAW_W):
                for y in range(16, bottom + 1):
                    cells.add((x, y))

    outline = set()
    for (x, y) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in cells:
                    outline.add(n)
    outline |= WHISKERS

    for p in outline:
        px[p] = "white"
    for p in cells:
        px[p] = "black"

    for (ex, ey) in (LEFT_EYE, RIGHT_EYE):
        if blink:
            for dx in range(2):
                px[(ex + dx, ey + 1)] = "white"
        else:
            for dx in range(2):
                for dy in range(2):
                    px[(ex + dx, ey + dy)] = "white"
            px[(ex + ox, ey + oy)] = "black"

    img = tk.PhotoImage(width=GRID_W, height=GRID_H)
    for (x, y), color in px.items():
        img.put(color, to=(x + 1, y + 1))
    return img.zoom(SCALE, SCALE)


class DesktopCat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        bg = TRANS
        if sys.platform.startswith("win"):
            self.root.attributes("-transparentcolor", TRANS)
        elif sys.platform == "darwin":
            self.root.attributes("-transparent", True)
            bg = "systemTransparent"
        self.root.config(bg=bg)

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H,
                                bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.item = self.canvas.create_image(0, 0, anchor="nw")

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{WIN_W}x{WIN_H}+{sw - WIN_W - 80}+{sh - WIN_H - 120}")

        # state
        self.cache = {}              # frames are built once, then reused
        self.last_key = 0.0
        self.last_move = time.time()
        self._mouse_pos = None
        self.paw = 0                 # which paw is down (0 left, 1 right)
        self.blink_until = 0.0
        self.next_blink = time.time() + random.uniform(2, 5)
        self._last_state = None
        self._drag = (0, 0)

        # dragging + menu
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Quit", command=self.quit)
        self.canvas.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
        self.canvas.bind("<Button-2>", lambda e: menu.tk_popup(e.x_root, e.y_root))  # mac

        # global key listener (runs in its own thread, only flags activity)
        self.listener = keyboard.Listener(on_press=self.on_key)
        self.listener.daemon = True
        self.listener.start()

        self.tick()

    # --- events ---------------------------------------------------------
    def on_key(self, _key):
        self.last_key = time.time()
        self.paw ^= 1

    def start_drag(self, e):
        self._drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def do_drag(self, e):
        self.root.geometry(f"+{e.x_root - self._drag[0]}+{e.y_root - self._drag[1]}")

    def quit(self):
        self.root.destroy()

    # --- main loop ------------------------------------------------------
    def show(self, state):
        img = self.cache.get(state)
        if img is None:
            img = self.cache[state] = render(*state)
        self.canvas.itemconfig(self.item, image=img)

    def tick(self):
        now = time.time()

        # eyes follow cursor
        mx, my = self.root.winfo_pointerxy()
        if (mx, my) != self._mouse_pos:
            self._mouse_pos = (mx, my)
            self.last_move = now
        cx = self.root.winfo_x() + WIN_W // 2
        cy = self.root.winfo_y() + int(WIN_H * 0.3)
        ox = 1 if mx > cx else 0
        oy = 1 if my > cy else 0

        # blink
        if now >= self.next_blink:
            self.blink_until = now + 0.15
            self.next_blink = now + random.uniform(2, 6)
        blink = now < self.blink_until

        typing = (now - self.last_key) < TYPING_TIMEOUT
        idle_for = now - max(self.last_move, self.last_key)
        if idle_for >= SLEEP_AFTER:
            # asleep: any mouse move or key press wakes the cat
            state = (0, 0, False, False, 0, True, int(now / 0.8) % 2)
        else:
            state = (ox, oy, blink, typing, self.paw if typing else 0, False, 0)
        if state != self._last_state:
            self._last_state = state
            self.show(state)

        self.root.after(40, self.tick)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DesktopCat().run()