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
    ("Thanks for watching", "PLEX"),
    ("Harrison wanted to get better at this on first date", "STORYTELLING"),
    ("Best beer", "JUBEL"),
    ("A swedish gift", "SKUNK"),
    ("Worst Edinburgh export", "COFFEE"),
    ("Thing make me throw up", "DORRITO"),
    ("Other thing make me throw up", "GALAXY"),
    ("Thing to do today", "MOVIE"),
    ("Hopefully later we watch", "MAFS"),
    ("In the can before bed", "CBD"),
    ("A goey dessert comes in a", "POT"),
    ("Perfect amount of dogs", "THREE"),
    ("The best kind of runner", "DUCK"),
    ("I ____ my bf", "HEART"),
]

FILLER = [
    ("Affection", "LOVE"),
    ("Warm hug", "CUDDLE"),
    ("Sweet bouquet", "ROSES"),
    ("Weekend meal", "BRUNCH"),
    ("Tiny love note", "POSTIT"),
    ("Chocolate type", "TRUFFLE"),
    ("Romantic promise", "FOREVER"),
    ("Night-sky light", "MOON"),
    ("Love message type", "TEXT"),
    ("Soft heartbeat sound", "THUMP"),
    ("Shared laugh", "GIGGLE"),
    ("Keep close", "HOLD"),
    ("Candle source", "WICK"),
    ("Sweet ending", "DESSERT"),
    ("Cozy weather", "RAINY"),
    ("Gift ribbon material", "SATIN"),
]

GRID = 44


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
    return min(rs), max(rs), min(cs), max(cs)


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


def attempt(seed):
    random.seed(seed)
    theme = sorted(THEME, key=lambda x: (-len(x[1]), x[1]))

    board = {}
    usage = {}
    placements = []

    clue0, w0 = theme[0]
    mid = GRID // 2
    c0 = mid - len(w0) // 2
    place(board, usage, w0, mid, c0, 'A')
    placements.append((clue0, w0, mid, c0, 'A', True))

    def bt(i):
        if i == len(theme):
            return True
        clue, word = theme[i]
        cands = gen_candidates(board, word)
        for r, c, d, _ in cands:
            changed = place(board, usage, word, r, c, d)
            placements.append((clue, word, r, c, d, True))
            if bt(i + 1):
                return True
            placements.pop()
            unplace(board, usage, changed, word, r, c, d)
        return False

    if not bt(1):
        return None

    used_words = {w for _, w, *_ in placements}
    fillers = FILLER[:]
    random.shuffle(fillers)

    for clue, word in fillers:
        if word in used_words:
            continue
        cands = gen_candidates(board, word)
        if not cands:
            continue
        r, c, d, inter = cands[0]
        if inter < 1:
            continue
        place(board, usage, word, r, c, d)
        placements.append((clue, word, r, c, d, False))
        used_words.add(word)

    r0, r1, c0, c1 = bounding(board)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    if h > 25 or w > 25:
        return None

    rows = [['#'] * w for _ in range(h)]
    for (r, c), ch in board.items():
        rows[r - r0][c - c0] = ch
    rows = [''.join(r) for r in rows]

    normalized = []
    for clue, word, r, c, d, is_theme in placements:
        normalized.append((clue, word, r - r0, c - c0, d, is_theme))

    across, down = enumerate_entries(rows)
    enum_words = {w for _, w, _, _ in across + down}
    placed_words = {w for _, w, *_ in normalized}
    theme_words = {w for _, w in THEME}

    if not theme_words.issubset(enum_words):
        return None
    if not enum_words.issubset(placed_words):
        return None

    clues = {ans: clue for clue, ans in THEME + FILLER}
    if any(w not in clues for _, w, _, _ in across + down):
        return None

    filler_count = sum(1 for _, w, *_ in normalized if w in enum_words and w not in theme_words)
    score = (filler_count, h * w, abs(h - w))
    return score, rows, across, down, filler_count


def main():
    best = None
    for seed in range(3500):
        out = attempt(seed)
        if not out:
            continue
        if best is None or out[0] < best[0]:
            best = out
            print('seed', seed, 'score', out[0], 'fillers', out[4], 'size', len(out[1]), 'x', len(out[1][0]))
            if out[4] <= 4:
                break

    if not best:
        print('NO_SOLUTION')
        return

    _, rows, across, down, filler_count = best
    clues = {ans: clue for clue, ans in THEME + FILLER}

    print('FINAL fillers', filler_count)
    print('ROWS = [')
    for r in rows:
        print(f'  "{r}",')
    print(']')

    print('ACROSS = {')
    for n, w, _, _ in across:
        print(f'  {n}: "{clues[w]}",')
    print('}')

    print('DOWN = {')
    for n, w, _, _ in down:
        print(f'  {n}: "{clues[w]}",')
    print('}')

    print('WORDS')
    for n, w, _, _ in across:
        print('A', n, w)
    for n, w, _, _ in down:
        print('D', n, w)

if __name__ == '__main__':
    main()
