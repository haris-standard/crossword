import random
import re
from collections import defaultdict, deque

SIZE = 13
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

def load_words():
    by_len = defaultdict(set)
    with open('/usr/share/dict/words', errors='ignore') as f:
        for raw in f:
            w = raw.strip()
            if not w.isalpha():
                continue
            if w.lower() != w:
                continue
            w = w.upper()
            if not (3 <= len(w) <= SIZE):
                continue
            if sum(ch in 'AEIOUY' for ch in w) == 0:
                continue
            if len(set(w)) <= 2 and len(w) > 4:
                continue
            by_len[len(w)].add(w)
    for _, ans in THEME:
        by_len[len(ans)].add(ans)
    return {k: sorted(v) for k, v in by_len.items()}

WORDS = load_words()

class Slot:
    def __init__(self, sid, direction, cells):
        self.sid = sid
        self.direction = direction
        self.cells = cells
        self.length = len(cells)


def mirrored(r, c):
    return SIZE - 1 - r, SIZE - 1 - c


def build_random_grid(block_prob=0.28):
    g = [[False] * SIZE for _ in range(SIZE)]
    for r in range((SIZE + 1) // 2):
        for c in range(SIZE):
            mr, mc = mirrored(r, c)
            if (r, c) > (mr, mc):
                continue
            b = random.random() < block_prob
            g[r][c] = b
            g[mr][mc] = b
    return g


def extract_slots(blocks):
    slots = []
    sid = 0
    # across
    for r in range(SIZE):
        c = 0
        while c < SIZE:
            if blocks[r][c]:
                c += 1
                continue
            start = c
            while c < SIZE and not blocks[r][c]:
                c += 1
            if c - start >= 3:
                cells = [(r, x) for x in range(start, c)]
                slots.append(Slot(sid, 'across', cells))
                sid += 1
    # down
    for c in range(SIZE):
        r = 0
        while r < SIZE:
            if blocks[r][c]:
                r += 1
                continue
            start = r
            while r < SIZE and not blocks[r][c]:
                r += 1
            if r - start >= 3:
                cells = [(x, c) for x in range(start, r)]
                slots.append(Slot(sid, 'down', cells))
                sid += 1
    return slots


def white_cells(blocks):
    return [(r, c) for r in range(SIZE) for c in range(SIZE) if not blocks[r][c]]


def connected(blocks):
    whites = white_cells(blocks)
    if not whites:
        return False
    s = whites[0]
    q = deque([s])
    seen = {s}
    while q:
        r, c = q.popleft()
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and not blocks[nr][nc] and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return len(seen) == len(whites)


def min_run_ok(blocks):
    # every white cell must belong to across and down runs length >=3
    for r in range(SIZE):
        for c in range(SIZE):
            if blocks[r][c]:
                continue
            a0 = c
            while a0 - 1 >= 0 and not blocks[r][a0 - 1]:
                a0 -= 1
            a1 = c
            while a1 + 1 < SIZE and not blocks[r][a1 + 1]:
                a1 += 1
            d0 = r
            while d0 - 1 >= 0 and not blocks[d0 - 1][c]:
                d0 -= 1
            d1 = r
            while d1 + 1 < SIZE and not blocks[d1 + 1][c]:
                d1 += 1
            if a1 - a0 + 1 < 3 or d1 - d0 + 1 < 3:
                return False
    return True


def valid_pattern(blocks):
    nwhite = len(white_cells(blocks))
    if nwhite < 70 or nwhite > 110:
        return False
    if not connected(blocks):
        return False
    if not min_run_ok(blocks):
        return False
    slots = extract_slots(blocks)
    if len(slots) < 20 or len(slots) > 40:
        return False
    return True


def build_crossings(slots):
    cell_to_slots = defaultdict(list)
    for s in slots:
        for idx, cell in enumerate(s.cells):
            cell_to_slots[cell].append((s.sid, idx))
    cross = defaultdict(list)
    for cell, refs in cell_to_slots.items():
        if len(refs) == 2:
            (s1, i1), (s2, i2) = refs
            cross[s1].append((i1, s2, i2))
            cross[s2].append((i2, s1, i1))
    return cross


def assign_theme_slots(slots):
    slots_by_len = defaultdict(list)
    for s in slots:
        slots_by_len[s.length].append(s.sid)

    themes = [(clue, ans) for clue, ans in THEME]
    themes.sort(key=lambda x: len(slots_by_len[len(x[1])]))

    used = set()
    mapping = {}

    def bt(i):
        if i == len(themes):
            return True
        _, ans = themes[i]
        cands = slots_by_len[len(ans)]
        random.shuffle(cands)
        for sid in cands:
            if sid in used:
                continue
            used.add(sid)
            mapping[sid] = ans
            if bt(i + 1):
                return True
            used.remove(sid)
            del mapping[sid]
        return False

    if bt(0):
        return mapping
    return None


def solve_fill(slots, forced):
    cross = build_crossings(slots)
    slot_by_id = {s.sid: s for s in slots}

    assignments = dict(forced)
    used_words = set(assignments.values())

    # Grid letters from forced assignments
    letters = {}
    for sid, w in assignments.items():
        s = slot_by_id[sid]
        for i, cell in enumerate(s.cells):
            ch = w[i]
            if cell in letters and letters[cell] != ch:
                return None
            letters[cell] = ch

    unfilled = [s.sid for s in slots if s.sid not in assignments]

    def candidates_for(sid):
        s = slot_by_id[sid]
        out = []
        for w in WORDS.get(s.length, []):
            if w in used_words:
                continue
            ok = True
            for i, cell in enumerate(s.cells):
                if cell in letters and letters[cell] != w[i]:
                    ok = False
                    break
            if ok:
                out.append(w)
        random.shuffle(out)
        return out[:250]  # prune to keep solve tractable

    def choose_slot():
        best_sid = None
        best_cands = None
        best_len = 10**9
        for sid in unfilled:
            cands = candidates_for(sid)
            ln = len(cands)
            if ln < best_len:
                best_len = ln
                best_sid = sid
                best_cands = cands
            if ln <= 1:
                break
        return best_sid, best_cands

    def bt():
        if not unfilled:
            return True
        sid, cands = choose_slot()
        if not cands:
            return False

        s = slot_by_id[sid]
        unfilled.remove(sid)

        for w in cands:
            changed = []
            conflict = False
            for i, cell in enumerate(s.cells):
                ch = w[i]
                prev = letters.get(cell)
                if prev is not None and prev != ch:
                    conflict = True
                    break
                if prev is None:
                    letters[cell] = ch
                    changed.append(cell)
            if conflict:
                for cell in changed:
                    del letters[cell]
                continue

            assignments[sid] = w
            used_words.add(w)

            if bt():
                return True

            del assignments[sid]
            used_words.remove(w)
            for cell in changed:
                del letters[cell]

        unfilled.append(sid)
        return False

    if bt():
        return assignments
    return None


def build_solution(blocks, slots, assignments):
    grid = [['#' if blocks[r][c] else '?' for c in range(SIZE)] for r in range(SIZE)]
    for s in slots:
        w = assignments[s.sid]
        for i, (r, c) in enumerate(s.cells):
            grid[r][c] = w[i]
    return [''.join(row) for row in grid]


def collect_entries(grid):
    across = []
    down = []
    num = 1
    numbers = {}
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c] == '#':
                continue
            starts_a = (c == 0 or grid[r][c-1] == '#') and (c+1 < SIZE and grid[r][c+1] != '#')
            starts_d = (r == 0 or grid[r-1][c] == '#') and (r+1 < SIZE and grid[r+1][c] != '#')
            if starts_a or starts_d:
                numbers[(r,c)] = num
                num += 1
            if starts_a:
                cc = c
                w = []
                while cc < SIZE and grid[r][cc] != '#':
                    w.append(grid[r][cc]); cc += 1
                across.append((numbers[(r,c)], ''.join(w), r, c))
            if starts_d:
                rr = r
                w = []
                while rr < SIZE and grid[rr][c] != '#':
                    w.append(grid[rr][c]); rr += 1
                down.append((numbers[(r,c)], ''.join(w), r, c))
    return across, down


def score_entries(across, down):
    entries = across + down
    penalty = 0
    bad_chunks = ['Q','X','Z','J']
    for _, w, _, _ in entries:
        if any(ch*3 in w for ch in set(w)):
            penalty += 3
        penalty += sum(w.count(ch) for ch in bad_chunks) * 0.5
        if len(set(w)) <= 2:
            penalty += 5
    return penalty


def main():
    best = None
    for attempt in range(1200):
        blocks = build_random_grid(block_prob=random.uniform(0.24, 0.34))
        if not valid_pattern(blocks):
            continue
        slots = extract_slots(blocks)
        forced = assign_theme_slots(slots)
        if not forced:
            continue
        assignments = solve_fill(slots, forced)
        if not assignments:
            continue
        grid = build_solution(blocks, slots, assignments)
        across, down = collect_entries(grid)
        theme_words = {a for _, a in THEME}
        all_words = {w for _, w, _, _ in across + down}
        if not theme_words.issubset(all_words):
            continue
        sc = score_entries(across, down)
        if best is None or sc < best[0]:
            best = (sc, grid, across, down)
            print('candidate', attempt, 'score', sc, 'across', len(across), 'down', len(down))
            if sc < 8:
                break

    if not best:
        print('NO SOLUTION')
        return

    _, grid, across, down = best
    print('GRID:')
    for r in grid:
        print(r)
    print('ACROSS:')
    for n,w,_,_ in across:
        print(n,w)
    print('DOWN:')
    for n,w,_,_ in down:
        print(n,w)

if __name__ == '__main__':
    main()
