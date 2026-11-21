#!/usr/bin/env python3
"""THE DAILY BLAST - the world news of 21 November 2026 on one page.

Pure Python standard library. A hand-rolled 5x7 bitmap typeface and a
small raster canvas are used to draw a tabloid front page, which is then
encoded as a PNG with zlib. No clock, no randomness, no network: the
output bytes are identical on every run.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Typeface: every glyph is seven rows of five pixels, '#' marks ink.
# ---------------------------------------------------------------------------

GLYPHS = {
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#..##", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": (".##..", "..#..", "...#.", "...#.", "...#.", "..#..", ".##.."),
    "$": ("..#..", ".####", "#.#.#", ".###.", "#.#.#", "####.", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "£": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", "#####"),
}

INK = "#"
BLANK_GLYPH = GLYPHS[" "]


def glyph_for(ch):
    return GLYPHS.get(ch, BLANK_GLYPH)


def text_width(s, scale):
    """Pixel width of a string: 5 ink columns plus one gap per character."""
    if not s:
        return 0
    return len(s) * 6 * scale - scale


# ---------------------------------------------------------------------------
# Canvas: a flat RGB pixel buffer with rectangle and text drawing.
# ---------------------------------------------------------------------------

WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (206, 17, 17)
DARKRED = (150, 8, 8)
YELLOW = (255, 208, 0)
GOLD = (255, 176, 0)
PAPER = (253, 250, 240)
PINK = (253, 233, 233)
GREY = (90, 90, 90)
LIGHT = (238, 238, 232)
GREEN = (8, 120, 52)


class Page:
    def __init__(self, width, height, bg=WHITE):
        self.w = width
        self.h = height
        self.px = bytearray(bg) * (width * height)
        self.y = 0  # deepest row painted so far (for the final crop)

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.px[off:off + len(row)] = row
        if y1 > self.y:
            self.y = y1

    def frame(self, x, y, w, h, color, thick):
        self.rect(x, y, w, thick, color)
        self.rect(x, y + h - thick, w, thick, color)
        self.rect(x, y, thick, h, color)
        self.rect(x + w - thick, y, thick, h, color)

    def draw_text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            rows = glyph_for(ch)
            for r in range(7):
                line = rows[r]
                for c in range(5):
                    if line[c] == INK:
                        self.rect(cx + c * scale, y + r * scale,
                                  scale, scale, color)
            cx += 6 * scale
        if s:
            bottom = y + 7 * scale
            if bottom > self.y:
                self.y = bottom
        return cx - scale - x if s else 0

    def centered(self, cx, y, s, scale, color):
        w = text_width(s, scale)
        return self.draw_text(cx - w // 2, y, s, scale, color)

    def wrap(self, s, scale, maxw):
        """Greedy word wrap against a pixel width."""
        words = s.split()
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def paragraph(self, x, y, s, scale, color, maxw, leading=None):
        step = leading if leading is not None else 10 * scale
        for line in self.wrap(s, scale, maxw):
            self.draw_text(x, y, line, scale, color)
            y += step
        return y

    def save(self, path, crop_to=None):
        height = self.h if crop_to is None else min(self.h, crop_to)
        raw = bytearray()
        stride = self.w * 3
        for yy in range(height):
            raw.append(0)
            raw += self.px[yy * stride:(yy + 1) * stride]

        def chunk(tag, data):
            body = tag + data
            return (struct.pack(">I", len(data)) + body +
                    struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

        png = bytearray(b"\x89PNG\r\n\x1a\n")
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, height,
                                          8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as fh:
            fh.write(bytes(png))


# ---------------------------------------------------------------------------
# Layout helpers.
# ---------------------------------------------------------------------------

W = 1240
MARGIN = 40
CW = W - 2 * MARGIN


def chip(page, x, y, label, scale=3, bg=BLACK, fg=YELLOW):
    w = text_width(label, scale) + 28
    h = 7 * scale + 20
    page.rect(x, y, w, h, bg)
    page.draw_text(x + 14, y + 10, label, scale, fg)
    return x + w + 14


def titled_panel(page, y, title, title_bg, title_fg, body_bg, paras,
                 scale=3, title_scale=5, fg=BLACK):
    pad = 22
    lines = 0
    for p in paras:
        lines += len(page.wrap(p, scale, CW - 2 * pad))
    title_h = 7 * title_scale + 22
    body_h = 16 + lines * 10 * scale + (len(paras) - 1) * 12 + 8
    page.rect(MARGIN, y, CW, title_h, title_bg)
    page.draw_text(MARGIN + pad, y + 11, title, title_scale, title_fg)
    top = y + title_h
    page.rect(MARGIN, top, CW, body_h, body_bg)
    cy = top + 16
    for p in paras:
        cy = page.paragraph(MARGIN + pad, cy, p, scale, fg, CW - 2 * pad)
        cy += 12
    page.frame(MARGIN, y, CW, title_h + body_h, BLACK, 4)
    return y + title_h + body_h


# ---------------------------------------------------------------------------
# The front page.
# ---------------------------------------------------------------------------

def build_page():
    page = Page(W, 3600, PAPER)

    # Red breaking-news banner.
    page.rect(0, 0, W, 70, RED)
    page.draw_text(MARGIN, 12, "BREAKING NEWS", 6, WHITE)
    date = "SATURDAY 21 NOVEMBER 2026"
    page.draw_text(W - MARGIN - text_width(date, 3), 22, date, 3, WHITE)

    # Black masthead.
    y = 70
    page.rect(0, y, W, 150, BLACK)
    page.centered(W // 2, y + 16, "THE DAILY BLAST", 12, YELLOW)
    page.centered(W // 2, y + 112, "THE WHOLE PLANET IN ONE PAGE", 3, WHITE)
    y += 150 + 26

    # ---- Lead story: missiles come down inside Poland. ----
    page.draw_text(MARGIN, y, "LEAD STORY - EUROPE ON THE EDGE", 4, RED)
    y += 7 * 4 + 14
    page.draw_text(MARGIN, y, "RUSSIAN MISSILES", 10, BLACK)
    y += 7 * 10 + 6
    page.draw_text(MARGIN, y, "CRASH INTO POLAND!", 10, RED)
    y += 7 * 10 + 20
    y = page.paragraph(
        MARGIN, y,
        "TWO MISSILES AND A SUSPECTED JET-POWERED DRONE CAME DOWN IN THE "
        "SOUTH-EAST OF POLAND - AND NATO JETS SCRAMBLED INTO THE SKY.",
        4, BLACK, CW)
    y += 8
    cx = MARGIN
    for lab in ("2 MISSILES DOWN", "1 DRONE DOWN", "0 HURT IN POLAND",
                "JETS SCRAMBLED"):
        cx = chip(page, cx, y, lab)
    y += 7 * 3 + 20 + 20
    y = page.paragraph(
        MARGIN, y,
        "ONE OF THE WRECKS WAS A KH-101 CRUISE MISSILE THAT CAME DOWN "
        "NEAR THE VILLAGE OF NOWY LIPOWIEC. NOBODY IN POLAND WAS HURT.",
        3, BLACK, CW)
    y += 4
    y = page.paragraph(
        MARGIN, y,
        "POLISH PM TUSK CALLED THE INTRUSION AN 'INTENTIONAL "
        "PROVOCATION'. NATO CHIEF RUTTE CALLED IT A 'GRAVE VIOLATION' "
        "OF ALLIED AIRSPACE.",
        3, BLACK, CW)

    # ---- Ukraine barrage block on pink. ----
    y += 16
    u_paras = [
        "OFFICIALS SAY AT LEAST 11 PEOPLE WERE KILLED AND DOZENS INJURED "
        "AS THE BARRAGE SLAMMED INTO TARGETS INCLUDING KYIV AND "
        "KRYVYI RIH.",
        "KRYVYI RIH TOOK A BRUTAL HIT: TWO DEAD - A BOY OF SEVEN AND A "
        "PARAMEDIC OF TWENTY - WITH 42 INJURED, FOUR OF THEM CHILDREN "
        "AND 27 IN SERIOUS CONDITION.",
    ]
    u_lines = 0
    for p in u_paras:
        u_lines += len(page.wrap(p, 3, CW - 44))
    u_h = 16 + 28 + 12 + (7 * 3 + 20) + 14 + u_lines * 30 + 12 + 14
    page.rect(MARGIN, y, CW, u_h, PINK)
    cy = y + 16
    page.draw_text(MARGIN + 22, cy, "UKRAINE UNDER FIRE - ZELENSKYY'S COUNT",
                   4, DARKRED)
    cy += 28 + 12
    cx = MARGIN + 22
    for lab in ("400+ DRONES", "110+ MISSILES", "27 BALLISTIC", "11+ KILLED"):
        cx = chip(page, cx, cy, lab, bg=DARKRED, fg=WHITE)
    cy += 7 * 3 + 20 + 14
    for p in u_paras:
        cy = page.paragraph(MARGIN + 22, cy, p, 3, BLACK, CW - 44)
        cy += 12
    page.frame(MARGIN, y, CW, u_h, RED, 4)
    y += u_h + 26

    # ---- Markets wipeout panel on black. ----
    m_paras = [
        "IT CLOSED AT 6,910.39 - MORE THAN 10% BELOW ITS 6 OCTOBER HIGH "
        "AND INTO CORRECTION TERRITORY. THE WORST WEEK IN 18+ MONTHS.",
        "THE NASDAQ PLUNGED -5.3% TO 22,617.73 AND IS NOW NEGATIVE FOR "
        "THE YEAR. THE DOW SLID -1.9% TO 48,147.33.",
        "CHIP KING NVIDIA TUMBLED -13.8%. AI DARLING ANTHROPIC DROPPED "
        "-9.1% JUST ONE DAY AFTER ITS RECORD DEBUT.",
        "ASIA CAUGHT THE FEVER TOO: TOKYO'S NIKKEI LOST -5.1% AND "
        "SEOUL'S KOSPI LOST -5.2%.",
    ]
    m_lines = 0
    for p in m_paras:
        m_lines += len(page.wrap(p, 3, CW - 44))
    m_h = 20 + 42 + 14 + 77 + 18 + m_lines * 30 + 3 * 12 + 16
    page.rect(MARGIN, y, CW, m_h, BLACK)
    cy = y + 20
    page.draw_text(MARGIN + 22, cy, "WALL STREET WIPEOUT!", 6, YELLOW)
    cy += 42 + 14
    page.draw_text(MARGIN + 22, cy, "S&P 500 -3.7%", 11, RED)
    cy += 77 + 18
    for p in m_paras:
        cy = page.paragraph(MARGIN + 22, cy, p, 3, WHITE, CW - 44)
        cy += 12
    y += m_h + 26

    # ---- Summit panel. ----
    y = titled_panel(
        page, y, "SUPERPOWER SUMMIT BOMBSHELL!", BLACK, YELLOW, LIGHT,
        [
            "TRUMP, XI AND PUTIN SAT DOWN AT ONE TABLE FOR THE FIRST "
            "TIME IN HISTORY - 19 NOVEMBER, AT KYLIN VILLA IN SHENZHEN, "
            "ON THE SIDELINES OF APEC.",
            "OUT OF IT CAME A FOUR-POINT 'DECLARATION TOWARD PEACE': "
            "UN REFORM, ENERGY SUPPLY, LIMITS ON THE ICC AND "
            "NUCLEAR-RISK TALKS.",
            "ONE WORD NEVER APPEARS IN THE TEXT: UKRAINE. NO PEACE "
            "DEAL WAS DONE.",
            "FT: THE WHITE HOUSE WANTS A KYIV PEACE DEAL BY EARLY "
            "JANUARY 2027 - BEFORE THE DEMOCRATS TAKE CONTROL OF "
            "CONGRESS.",
        ]) + 26

    # ---- World Court panel. ----
    y = titled_panel(
        page, y, "WORLD COURT: GENOCIDE!", DARKRED, WHITE, LIGHT,
        [
            "THE INTERNATIONAL COURT OF JUSTICE RULED BY 9 VOTES TO 6 "
            "THAT MYANMAR COMMITTED GENOCIDE AGAINST THE ROHINGYA IN "
            "ITS 2017 CLEARANCE OPERATIONS.",
            "THE COURT ORDERED RESTITUTION, WITH A REPORT DUE WITHIN "
            "TWO YEARS.",
            "A FIRST IN HISTORY: NEVER BEFORE HAS THE WORLD COURT HELD "
            "A STATE RESPONSIBLE FOR COMMITTING GENOCIDE ITSELF.",
        ]) + 26

    # ---- UK-EU deals panel. ----
    y = titled_panel(
        page, y, "UK-EU MEGA-DEALS SIGNED!", BLACK, GOLD, LIGHT,
        [
            "LONDON AND BRUSSELS SEALED THREE DEALS IN BRUSSELS ON "
            "20 NOVEMBER: FOOD TRADE, A CARBON-TRADING LINK AND YOUTH "
            "MOBILITY.",
            "PM ANDY BURNHAM'S FOOD DEAL COULD BE WORTH UP TO £5.1BN "
            "A YEAR, ON UK ESTIMATES.",
            "THE YOUTH SCHEME OPENS 100,000 PLACES A YEAR ON EACH SIDE.",
        ]) + 26

    # ---- COP31 band on yellow. ----
    y = titled_panel(
        page, y, "COP31 SHOCKER - FOSSIL FUELS VANISH!", YELLOW, BLACK,
        YELLOW,
        [
            "THE ANTALYA CLIMATE SUMMIT CLOSED ON 20 NOVEMBER WITH A "
            "FINAL TEXT THAT NEVER ONCE MENTIONS FOSSIL FUELS.",
            "THE $120BN-A-YEAR ADAPTATION TARGET WAS DROPPED - BUT "
            "THE CALL TO AT LEAST TRIPLE ADAPTATION FINANCE BY 2035 "
            "SURVIVED.",
            "ELECTRICITY IS TO REACH 35% OF ALL FINAL ENERGY USE BY "
            "2035, UP FROM ABOUT 23% TODAY.",
        ]) + 26

    # ---- Ticker on black. ----
    t_paras = [
        "* PALISADES ARSONIST CONVICTED: A LOS ANGELES FEDERAL JURY "
        "FOUND JONATHAN RINDERKNECHT, 30, GUILTY OF ARSON OVER THE "
        "JANUARY 2025 FIRE THAT KILLED 12. HE FACES UP TO 40 YEARS - "
        "SENTENCING IS SET FOR 17 MARCH 2027.",
        "* CANCER PILL SENSATION: DARAXONRASIB STOPPED TUMOURS GROWING "
        "IN 90.2% OF 61 TRIAL PATIENTS - AND IN 1 IN 12 THE TUMOURS "
        "COULD NO LONGER BE FOUND AT ALL.",
        "* MISSILES OVER RIYADH: THE SAUDI-LED COALITION DESTROYED 3 "
        "HOUTHI BALLISTIC MISSILES FIRED AT THE CAPITAL AND STRUCK "
        "BACK AT HODEIDAH. A TANKER CAUGHT FIRE 8 NAUTICAL MILES NORTH "
        "OF KHASAB, BY THE STRAIT OF HORMUZ.",
        "* TRUMP ON IRAN: 'I AM NOT RUSHING TO MAKE ANY DECISIONS' - A "
        "CALL ON IRAN MAY WAIT UNTIL AFTER 1 JANUARY, INTO 2027.",
    ]
    t_lines = 0
    for p in t_paras:
        t_lines += len(page.wrap(p, 3, CW - 44))
    t_h = 18 + 28 + 12 + t_lines * 30 + 3 * 12 + 14
    page.rect(MARGIN, y, CW, t_h, BLACK)
    cy = y + 18
    page.draw_text(MARGIN + 22, cy, "ALSO TODAY - THE TICKER", 4, GOLD)
    cy += 28 + 12
    for p in t_paras:
        cy = page.paragraph(MARGIN + 22, cy, p, 3, WHITE, CW - 44)
        cy += 12
    y += t_h + 22

    # ---- Footer. ----
    page.centered(W // 2, y,
                  "SOURCES: REUTERS - AP - RFE/RL - UKRINFORM - "
                  "THE GUARDIAN - FT - US DOJ", 2, GREY)
    return page


def main():
    page = build_page()
    here = os.path.dirname(os.path.abspath(__file__))
    height = page.y + 30
    local = os.path.join(here, "entry.png")
    page.save(local, crop_to=height)
    try:
        os.makedirs("/output", exist_ok=True)
        page.save(os.path.join("/output", "entry.png"), crop_to=height)
    except OSError:
        pass
    print("wrote", local)


if __name__ == "__main__":
    main()
