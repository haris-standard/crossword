import random
from collections import defaultdict

THEME = [
    ("First date location", "BRICKLANE"),
    ("How we first opened up", "HINGE"),
    ("Harrison's bubble tea order", "MANGOGREENTEA"),
    ("The child she made for me", "BOBBER"),
    ("Bad Knolly's small-talk topics", "STAIRCOUNT"),
    ("Anniversary", "MAYTWENTYITH"),
    ("Name in my phone", "JORDANA"),
    ("Best thing for before bed", "GETRILED"),
    ("Second best thing for before bed", "BEDTIMEDRINK"),
    ("Favorite thing for dinner", "UBEREAT"),
]

FILL = [
    ("Romance itself", "LOVE"),
    ("Valentine shape", "HEART"),
    ("Date-night gesture", "KISS"),
    ("Warm embrace", "CUDDLE"),
    ("Big grin", "SMILE"),
    ("Sweet flowers", "ROSES"),
    ("Evening meal", "DINNER"),
    ("A fun outing", "DATE"),
    ("What we do together", "LAUGH"),
    ("Tiny spark", "CHEMISTRY"),
    ("Caffeine pick-me-up", "COFFEE"),
    ("Shared promise", "FOREVER"),
    ("Movie-night snack", "POPCORN"),
    ("Goodnight phrase", "SWEETDREAMS"),
    ("A little adventure", "ROADTRIP"),
    ("Weekend activity", "BRUNCH"),
    ("Late-night craving", "SNACK"),
    ("Long walk destination", "PARK"),
    ("Tiny reminder note", "POSTIT"),
    ("Photo memory", "SELFIE"),
    ("Saturday plan", "PICNIC"),
    ("Cozy weather", "RAINY"),
    ("Couple selfie mode", "PORTRAIT"),
    ("A thoughtful gift", "PRESENT"),
]

WORDS = THEME + FILL
GRID = 31

random.seed(10)

class Placement:
    def __init__(self, clue, word, r, c, d):
        self.clue = clue
        self.word = word
        self.r = r
        self.c = c
        self.d = d  # 'A' or 'D'

    def cells(self):
        out = []
        for i, ch in enumerate(self.word):
            rr = self.r + (i if self.d == 'D' else 0)
            cc = self.c + (i if self.d == 'A' else 0)
            out.append((rr, cc, ch))
        return out


def in_bounds(r, c):
    return 0 <= r < GRID and 0 <= c < GRID


def can_place(board, word, r, c, d):
    dr, dc = (0, 1) if d == 'A' else (1, 0)
    # endpoints must be clear
    br, bc = r - dr, c - dc
    ar, ac = r + dr * len(word), c + dc * len(word)
    if in_bounds(br, bc) and board.get((br, bc)):
        return False
    if in_bounds(ar, ac) and board.get((ar, ac)):
        return False

    intersects = 0
    for i, ch in enumerate(word):
        rr = r + dr * i
        cc = c + dc * i
        if not in_bounds(rr, cc):
            return False
        existing = board.get((rr, cc))
        if existing and existing != ch:
            return False
        if existing == ch:
            intersects += 1

        # side-adjacency rule to avoid accidental words
        if d == 'A':
            for sr in (rr - 1, rr + 1):
                if in_bounds(sr, cc) and board.get((sr, cc)):
                    if existing != ch:  # allow only at crossing cell
                        return False
        else:
            for sc in (cc - 1, cc + 1):
                if in_bounds(rr, sc) and board.get((rr, sc)):
                    if existing != ch:
                        return False

    return intersects


def place_word(board, placement):
    for r, c, ch in placement.cells():
        board[(r, c)] = ch


def remove_word(board, placement, usage):
    for r, c, _ in placement.cells():
        usage[(r, c)] -= 1
        if usage[(r, c)] == 0:
            del usage[(r, c)]
            del board[(r, c)]


def add_word(board, placement, usage):
    for r, c, ch in placement.cells():
        board[(r, c)] = ch
        usage[(r, c)] = usage.get((r, c), 0) + 1


def candidate_positions(board, word):
    if not board:
        mid = GRID // 2
        return [(mid, max(1, mid - len(word)//2), 'A', 0)]

    by_char = defaultdict(list)
    for (r, c), ch in board.items():
        by_char[ch].append((r, c))

    out = set()
    for i, ch in enumerate(word):
        for r, c in by_char.get(ch, []):
            # place across
            rr, cc = r, c - i
            inter = can_place(board, word, rr, cc, 'A')
            if inter:
                out.add((rr, cc, 'A', inter))
            # place down
            rr, cc = r - i, c
            inter = can_place(board, word, rr, cc, 'D')
            if inter:
                out.add((rr, cc, 'D', inter))

    # prioritize more intersections
    return sorted(out, key=lambda x: (-x[3], random.random()))


def build():
    words = WORDS[:]
    # longest first is usually stable
    words.sort(key=lambda x: (-len(x[1]), x[1]))

    board = {}
    usage = {}
    placements = []

    def bt(i):
        if i == len(words):
            return True
        clue, word = words[i]
        cands = candidate_positions(board, word)
        if i > 0:
            cands = [c for c in cands if c[3] > 0]
        for r, c, d, _ in cands:
            p = Placement(clue, word, r, c, d)
            add_word(board, p, usage)
            placements.append(p)
            if bt(i + 1):
                return True
            placements.pop()
            remove_word(board, p, usage)
        return False

    ok = bt(0)
    if not ok:
        return None

    # crop bounds
    rs = [r for (r, _) in board.keys()]
    cs = [c for (_, c) in board.keys()]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)

    h = r1 - r0 + 1
    w = c1 - c0 + 1

    grid = [['#'] * w for _ in range(h)]
    for (r, c), ch in board.items():
        grid[r - r0][c - c0] = ch

    # normalize placements to cropped coords
    norm = []
    for p in placements:
        norm.append(Placement(p.clue, p.word, p.r - r0, p.c - c0, p.d))

    return [''.join(row) for row in grid], norm


def enumerate_entries(rows):
    h = len(rows)
    w = len(rows[0])
    nums = {}
    n = 1
    across = []
    down = []

    for r in range(h):
        for c in range(w):
            if rows[r][c] == '#':
                continue
            sa = (c == 0 or rows[r][c-1] == '#') and c + 1 < w and rows[r][c+1] != '#'
            sd = (r == 0 or rows[r-1][c] == '#') and r + 1 < h and rows[r+1][c] != '#'
            if sa or sd:
                nums[(r, c)] = n
                n += 1
            if sa:
                cc = c
                wv = []
                while cc < w and rows[r][cc] != '#':
                    wv.append(rows[r][cc]); cc += 1
                across.append((nums[(r, c)], ''.join(wv), r, c))
            if sd:
                rr = r
                wv = []
                while rr < h and rows[rr][c] != '#':
                    wv.append(rows[rr][c]); rr += 1
                down.append((nums[(r, c)], ''.join(wv), r, c))
    return across, down


def main():
    best = None
    for _ in range(80):
        out = build()
        if not out:
            continue
        rows, placements = out
        if len(rows) > 21 or len(rows[0]) > 21:
            continue

        across, down = enumerate_entries(rows)
        words = {w for _, w, _, _ in across + down}
        theme_words = {w for _, w in THEME}
        if not theme_words.issubset(words):
            continue

        # ensure every entry is in our placed word list (no accidental fake entries)
        placed = {p.word for p in placements}
        if not all(w in placed for _, w, _, _ in across + down):
            continue

        # compactness score
        score = len(rows) * len(rows[0])
        if best is None or score < best[0]:
            best = (score, rows, across, down)

    if not best:
        print('NO_LAYOUT')
        return

    _, rows, across, down = best
    print('SIZE', len(rows), len(rows[0]))
    print('GRID')
    for r in rows:
        print(r)
    print('ACROSS')
    for n, w, r, c in across:
        print(n, w, r, c)
    print('DOWN')
    for n, w, r, c in down:
        print(n, w, r, c)

if __name__ == '__main__':
    main()
