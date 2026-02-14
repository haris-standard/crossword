import random
from collections import defaultdict, deque

SIZE = 15
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

random.seed(7)

def load_words():
    by_len = defaultdict(set)
    with open('/usr/share/dict/words', errors='ignore') as f:
        for raw in f:
            w = raw.strip()
            if not w.isalpha() or w.lower() != w:
                continue
            w = w.upper()
            L = len(w)
            if L < 3 or L > SIZE:
                continue
            if sum(ch in 'AEIOUY' for ch in w) == 0:
                continue
            if len(set(w)) <= 2 and L > 4:
                continue
            # trim very weird words
            weird = sum(ch in 'JQXZ' for ch in w)
            if weird > 2:
                continue
            by_len[L].add(w)
    for _, ans in THEME:
        by_len[len(ans)].add(ans)
    # shrink huge buckets to keep search tractable
    out = {}
    for L, ws in by_len.items():
        ws = sorted(ws)
        if len(ws) > 12000:
            # sample deterministic-ish spread
            step = len(ws) / 12000
            picked = []
            x = 0.0
            while len(picked) < 12000 and int(x) < len(ws):
                picked.append(ws[int(x)])
                x += step
            ws = picked
        out[L] = ws
    return out

WORDS = load_words()

class Slot:
    __slots__ = ("sid", "direction", "cells", "length")
    def __init__(self, sid, direction, cells):
        self.sid = sid
        self.direction = direction
        self.cells = cells
        self.length = len(cells)

def mirror(r, c):
    return SIZE - 1 - r, SIZE - 1 - c


def rand_blocks(p):
    b = [[False]*SIZE for _ in range(SIZE)]
    for r in range((SIZE+1)//2):
        for c in range(SIZE):
            mr, mc = mirror(r, c)
            if (r, c) > (mr, mc):
                continue
            v = random.random() < p
            b[r][c] = v
            b[mr][mc] = v
    return b


def white_list(b):
    return [(r,c) for r in range(SIZE) for c in range(SIZE) if not b[r][c]]


def is_connected(b):
    whites = white_list(b)
    if not whites:
        return False
    q = deque([whites[0]])
    seen = {whites[0]}
    while q:
        r,c = q.popleft()
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc = r+dr, c+dc
            if 0<=nr<SIZE and 0<=nc<SIZE and not b[nr][nc] and (nr,nc) not in seen:
                seen.add((nr,nc)); q.append((nr,nc))
    return len(seen)==len(whites)


def runs_ok(b):
    for r in range(SIZE):
        c=0
        while c<SIZE:
            if b[r][c]:
                c+=1; continue
            s=c
            while c<SIZE and not b[r][c]: c+=1
            if c-s<3: return False
    for c in range(SIZE):
        r=0
        while r<SIZE:
            if b[r][c]:
                r+=1; continue
            s=r
            while r<SIZE and not b[r][c]: r+=1
            if r-s<3: return False
    return True


def extract_slots(b):
    slots=[]; sid=0
    for r in range(SIZE):
        c=0
        while c<SIZE:
            if b[r][c]: c+=1; continue
            s=c
            while c<SIZE and not b[r][c]: c+=1
            if c-s>=3:
                slots.append(Slot(sid,'across',[(r,x) for x in range(s,c)])); sid+=1
    for c in range(SIZE):
        r=0
        while r<SIZE:
            if b[r][c]: r+=1; continue
            s=r
            while r<SIZE and not b[r][c]: r+=1
            if r-s>=3:
                slots.append(Slot(sid,'down',[(x,c) for x in range(s,r)])); sid+=1
    return slots


def valid_pattern(b):
    nwhite = len(white_list(b))
    if nwhite < 95 or nwhite > 145:
        return False
    if not is_connected(b):
        return False
    if not runs_ok(b):
        return False
    slots = extract_slots(b)
    if len(slots) < 38 or len(slots) > 72:
        return False
    lengths = defaultdict(int)
    for s in slots:
        lengths[s.length]+=1
    for _, ans in THEME:
        if lengths[len(ans)]==0:
            return False
    return True


def theme_to_slots(slots):
    by_len=defaultdict(list)
    for s in slots:
        by_len[s.length].append(s.sid)
    themes = sorted(THEME, key=lambda t: len(by_len[len(t[1])]))
    used=set(); mapping={}
    def bt(i):
        if i==len(themes): return True
        _,ans = themes[i]
        cands=by_len[len(ans)][:]
        random.shuffle(cands)
        for sid in cands:
            if sid in used: continue
            used.add(sid); mapping[sid]=ans
            if bt(i+1): return True
            used.remove(sid); del mapping[sid]
        return False
    return mapping if bt(0) else None


def build_indexes(words_by_len):
    idx = {}
    for L, ws in words_by_len.items():
        pos = [defaultdict(set) for _ in range(L)]
        for i,w in enumerate(ws):
            for p,ch in enumerate(w):
                pos[p][ch].add(i)
        idx[L] = (ws, pos)
    return idx

INDEX = build_indexes(WORDS)


def solve(slots, forced):
    slot_map={s.sid:s for s in slots}
    cell_refs=defaultdict(list)
    for s in slots:
        for i,cell in enumerate(s.cells):
            cell_refs[cell].append((s.sid,i))

    letters={}
    assign=dict(forced)
    used=set(assign.values())

    for sid,w in forced.items():
        s=slot_map[sid]
        for i,cell in enumerate(s.cells):
            ch=w[i]
            if cell in letters and letters[cell]!=ch:
                return None
            letters[cell]=ch

    unfilled=[s.sid for s in slots if s.sid not in assign]

    cache={}
    def candidates(sid):
        key=(sid,tuple(sorted((cell,ch) for cell,ch in letters.items() if cell in set(slot_map[sid].cells))))
        if key in cache:
            return cache[key]
        s=slot_map[sid]
        L=s.length
        if L not in INDEX:
            cache[key]=[]; return []
        ws,pos=INDEX[L]
        possible=None
        for i,cell in enumerate(s.cells):
            ch=letters.get(cell)
            if ch is None:
                continue
            ids=pos[i].get(ch,set())
            if possible is None:
                possible=set(ids)
            else:
                possible &= ids
            if not possible:
                cache[key]=[]; return []
        if possible is None:
            ids=range(len(ws))
        else:
            ids=possible
        out=[]
        for wi in ids:
            w=ws[wi]
            if w in used:
                continue
            out.append(w)
        # heuristic ordering: more vowels first
        out.sort(key=lambda w:(sum(ch in 'AEIOU' for ch in w), -len(set(w))), reverse=True)
        if len(out)>350:
            out=out[:350]
        cache[key]=out
        return out

    def choose():
        best=None; bestc=None; bestn=10**9
        for sid in unfilled:
            c=candidates(sid)
            n=len(c)
            if n<bestn:
                bestn=n; best=sid; bestc=c
            if n<=1:
                break
        return best,bestc

    def bt(depth=0):
        if not unfilled:
            return True
        sid,cands=choose()
        if not cands:
            return False
        s=slot_map[sid]
        unfilled.remove(sid)
        for w in cands:
            changed=[]
            bad=False
            for i,cell in enumerate(s.cells):
                ch=w[i]
                prev=letters.get(cell)
                if prev is not None and prev!=ch:
                    bad=True; break
                if prev is None:
                    letters[cell]=ch; changed.append(cell)
            if bad:
                for cell in changed: del letters[cell]
                continue
            assign[sid]=w; used.add(w)
            if bt(depth+1):
                return True
            del assign[sid]; used.remove(w)
            for cell in changed: del letters[cell]
        unfilled.append(sid)
        return False

    if bt():
        return assign
    return None


def make_grid(blocks, slots, assign):
    g=[['#' if blocks[r][c] else '?' for c in range(SIZE)] for r in range(SIZE)]
    for s in slots:
        w=assign[s.sid]
        for i,(r,c) in enumerate(s.cells):
            g[r][c]=w[i]
    return [''.join(r) for r in g]


def collect(grid):
    across=[]; down=[]; nums={}; n=1
    for r in range(SIZE):
        for c in range(SIZE):
            if grid[r][c]=='#': continue
            sa=(c==0 or grid[r][c-1]=='#') and (c+1<SIZE and grid[r][c+1]!='#')
            sd=(r==0 or grid[r-1][c]=='#') and (r+1<SIZE and grid[r+1][c]!='#')
            if sa or sd:
                nums[(r,c)]=n; n+=1
            if sa:
                cc=c; w=[]
                while cc<SIZE and grid[r][cc]!='#': w.append(grid[r][cc]); cc+=1
                across.append((nums[(r,c)], ''.join(w), r, c))
            if sd:
                rr=r; w=[]
                while rr<SIZE and grid[rr][c]!='#': w.append(grid[rr][c]); rr+=1
                down.append((nums[(r,c)], ''.join(w), r, c))
    return across,down


def main():
    best=None
    for att in range(800):
        blocks=rand_blocks(random.uniform(0.23,0.31))
        if not valid_pattern(blocks):
            continue
        slots=extract_slots(blocks)
        forced=theme_to_slots(slots)
        if not forced:
            continue
        assign=solve(slots, forced)
        if not assign:
            continue
        grid=make_grid(blocks,slots,assign)
        across,down=collect(grid)
        words={w for _,w,_,_ in across+down}
        if not all(ans in words for _,ans in THEME):
            continue
        # score weirdness
        bad=0
        for _,w,_,_ in across+down:
            bad += sum(ch in 'JQXZ' for ch in w)
            if len(set(w))<=2: bad+=3
        if best is None or bad<best[0]:
            best=(bad,grid,across,down)
            print('candidate',att,'bad',bad,'across',len(across),'down',len(down))
            if bad<=6:
                break
    if not best:
        print('NO SOLUTION'); return
    bad,grid,across,down=best
    print('BEST_BAD',bad)
    print('GRID')
    for r in grid: print(r)
    print('ACROSS')
    for n,w,_,_ in across: print(n,w)
    print('DOWN')
    for n,w,_,_ in down: print(n,w)

if __name__=='__main__':
    main()
