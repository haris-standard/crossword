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

FILLER = [
    ("Affection", "LOVE"),
    ("Valentine shape", "HEART"),
    ("Sweet bouquet", "ROSES"),
    ("Date-night outing", "MOVIE"),
    ("Warm hug", "CUDDLE"),
    ("Great chemistry", "SPARK"),
    ("Weekend meal", "BRUNCH"),
    ("Photo pose", "SELFIE"),
    ("Evening meal", "DINNER"),
    ("Shared laugh", "GIGGLE"),
    ("Cozy weather", "RAINY"),
    ("Morning drink", "COFFEE"),
    ("Sweet ending", "DESSERT"),
    ("Tiny love note", "POSTIT"),
    ("Gift ribbon material", "SATIN"),
    ("Romantic promise", "FOREVER"),
    ("Weekend escape", "ROADTRIP"),
    ("Night-sky light", "MOON"),
    ("Candle source", "WICK"),
    ("Love message type", "TEXT"),
    ("Keep close", "HOLD"),
    ("Chocolate type", "TRUFFLE"),
    ("Favorite app ping", "NOTIFICATION"),
    ("Soft heartbeat sound", "THUMP"),
]

GRID = 33

def in_bounds(r, c):
    return 0 <= r < GRID and 0 <= c < GRID


def can_place(board, word, r, c, d):
    dr, dc = (0, 1) if d == 'A' else (1, 0)
    br, bc = r - dr, c - dc
    ar, ac = r + dr * len(word), c + dc * len(word)
    if in_bounds(br, bc) and (br, bc) in board:
        return 0
    if in_bounds(ar, ac) and (ar, ac) in board:
        return 0

    inter = 0
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        if not in_bounds(rr, cc):
            return 0
        cur = board.get((rr, cc))
        if cur and cur != ch:
            return 0
        if cur == ch:
            inter += 1

        if d == 'A':
            for sr in (rr - 1, rr + 1):
                if in_bounds(sr, cc) and (sr, cc) in board and cur != ch:
                    return 0
        else:
            for sc in (cc - 1, cc + 1):
                if in_bounds(rr, sc) and (rr, sc) in board and cur != ch:
                    return 0

    return inter


def gen_candidates(board, word):
    if not board:
        mid = GRID // 2
        return [(mid, mid - len(word) // 2, 'A', 0)]

    by_char = defaultdict(list)
    for (r, c), ch in board.items():
        by_char[ch].append((r, c))

    out = []
    seen = set()
    for i, ch in enumerate(word):
        for r, c in by_char.get(ch, []):
            aa = (r, c - i, 'A')
            if aa not in seen:
                seen.add(aa)
                inter = can_place(board, word, r, c - i, 'A')
                if inter > 0:
                    out.append((r, c - i, 'A', inter))
            dd = (r - i, c, 'D')
            if dd not in seen:
                seen.add(dd)
                inter = can_place(board, word, r - i, c, 'D')
                if inter > 0:
                    out.append((r - i, c, 'D', inter))

    random.shuffle(out)
    out.sort(key=lambda x: -x[3])
    return out


def place(board, usage, word, r, c, d):
    dr, dc = (0, 1) if d == 'A' else (1, 0)
    changed = []
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        if (rr, cc) not in board:
            changed.append((rr, cc))
            board[(rr, cc)] = ch
        usage[(rr, cc)] = usage.get((rr, cc), 0) + 1
    return changed


def unplace(board, usage, changed, word, r, c, d):
    dr, dc = (0, 1) if d == 'A' else (1, 0)
    for i, _ in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        usage[(rr, cc)] -= 1
        if usage[(rr, cc)] == 0:
            del usage[(rr, cc)]
    for cell in changed:
        del board[cell]


def bounding(board):
    rs = [r for (r, _) in board]
    cs = [c for (_, c) in board]
    r0, r1 = min(rs), max(rs)
    c0, c1 = min(cs), max(cs)
    return r0, r1, c0, c1


def build(seed):
    random.seed(seed)
    theme = sorted(THEME, key=lambda x: (-len(x[1]), x[1]))

    board = {}
    usage = {}
    placements = []

    # place first word centered
    clue0, w0 = theme[0]
    mid = GRID // 2
    c0 = mid - len(w0)//2
    changed = place(board, usage, w0, mid, c0, 'A')
    placements.append((clue0, w0, mid, c0, 'A'))

    def bt(i):
        if i == len(theme):
            return True
        clue, word = theme[i]
        cands = gen_candidates(board, word)
        for r, c, d, inter in cands:
            changed = place(board, usage, word, r, c, d)
            placements.append((clue, word, r, c, d))
            if bt(i + 1):
                return True
            placements.pop()
            unplace(board, usage, changed, word, r, c, d)
        return False

    if not bt(1):
        return None

    # Greedily add filler words
    used_words = {w for _, w, *_ in placements}
    fillers = FILLER[:]
    random.shuffle(fillers)
    added = 0
    for clue, word in fillers:
        if word in used_words:
            continue
        cands = gen_candidates(board, word)
        if not cands:
            continue
        r, c, d, inter = cands[0]
        if inter < 1:
            continue
        changed = place(board, usage, word, r, c, d)
        placements.append((clue, word, r, c, d))
        used_words.add(word)
        added += 1

    r0, r1, c0, c1 = bounding(board)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    if h > 23 or w > 23:
        return None

    rows = [['#'] * w for _ in range(h)]
    for (r, c), ch in board.items():
        rows[r - r0][c - c0] = ch
    rows = [''.join(r) for r in rows]

    norm = []
    for clue, word, r, c, d in placements:
        norm.append((clue, word, r - r0, c - c0, d))

    return rows, norm, added


def enumerate_entries(rows):
    h, w = len(rows), len(rows[0])
    nums = {}
    n = 1
    across = []
    down = []

    for r in range(h):
        for c in range(w):
            if rows[r][c] == '#':
                continue
            sa = (c == 0 or rows[r][c - 1] == '#') and c + 1 < w and rows[r][c + 1] != '#'
            sd = (r == 0 or rows[r - 1][c] == '#') and r + 1 < h and rows[r + 1][c] != '#'
            if sa or sd:
                nums[(r, c)] = n
                n += 1
            if sa:
                cc = c
                word = []
                while cc < w and rows[r][cc] != '#':
                    word.append(rows[r][cc]); cc += 1
                across.append((nums[(r, c)], ''.join(word), r, c))
            if sd:
                rr = r
                word = []
                while rr < h and rows[rr][c] != '#':
                    word.append(rows[rr][c]); rr += 1
                down.append((nums[(r, c)], ''.join(word), r, c))
    return across, down


def main():
    best = None
    for seed in range(500):
        out = build(seed)
        if not out:
            continue
        rows, placements, added = out
        across, down = enumerate_entries(rows)
        placed_words = {w for _, w, *_ in placements}
        enum_words = {w for _, w, *_ in across + down}

        theme_words = {w for _, w in THEME}
        if not theme_words.issubset(enum_words):
            continue
        # no fake entries
        if not enum_words.issubset(placed_words):
            continue

        # all entries intersect at least once
        # by construction every non-first word intersects; ensure first intersects too
        inter_count = defaultdict(int)
        cell_map = defaultdict(list)
        for clue, word, r, c, d in placements:
            for i, ch in enumerate(word):
                rr = r + (i if d == 'D' else 0)
                cc = c + (i if d == 'A' else 0)
                cell_map[(rr, cc)].append(word)
        for words in cell_map.values():
            if len(words) > 1:
                for w in set(words):
                    inter_count[w] += 1
        if any(inter_count[w] == 0 for w in theme_words):
            continue

        h, w = len(rows), len(rows[0])
        score = (-(added), h * w, abs(h - w))
        if best is None or score < best[0]:
            best = (score, rows, placements, across, down, added)

    if not best:
        print('NO_FINAL')
        return

    _, rows, placements, across, down, added = best
    print('ROWS', len(rows), 'COLS', len(rows[0]), 'FILLERS_USED', added)
    print('GRID')
    for r in rows:
        print(r)

    clues = {ans: clue for clue, ans in THEME + FILLER}
    print('ACROSS')
    for n, w, _, _ in across:
        print(n, w, '|', clues.get(w, f'Filler word: {w.title()}'))
    print('DOWN')
    for n, w, _, _ in down:
        print(n, w, '|', clues.get(w, f'Filler word: {w.title()}'))

if __name__ == '__main__':
    main()
