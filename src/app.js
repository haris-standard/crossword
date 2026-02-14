import { puzzle } from "./puzzle.js";

const boardEl = document.getElementById("board");
const keyboardEl = document.getElementById("keyboard");
const activeClueEl = document.getElementById("activeClue");
const prevClueEl = document.getElementById("prevClue");
const nextClueEl = document.getElementById("nextClue");
const messageEl = document.getElementById("message");
const timerEl = document.getElementById("timer");
const directionBadgeEl = document.getElementById("directionBadge");
const settingsMenuEl = document.getElementById("settingsMenu");

const ROWS = puzzle.rows.length;
const COLS = puzzle.rows[0].length;
const solution = puzzle.rows.map((row) => row.split(""));
const entries = solution.map((row) => row.map((cell) => (cell === "#" ? "#" : "")));
const marks = solution.map((row) => row.map(() => ""));
const cellEls = Array.from({ length: ROWS }, () => Array(COLS).fill(null));
const letterEls = Array.from({ length: ROWS }, () => Array(COLS).fill(null));

let direction = "across";
let active = findFirstOpenCell();
let activeClueNumber = null;
let seconds = 0;
let timerId = null;
let hasCelebrated = false;

const numbering = buildNumbering(solution);
const clueStarts = buildClueStarts(solution, numbering);
setInitialSelection();
initializeBoard();
buildKeyboard();
bindActions();
startTimer();
render();

function bindActions() {
  document.getElementById("toggleDirection").addEventListener("click", () => {
    toggleDirection();
    closeSettingsMenu();
  });

  document.getElementById("checkPuzzle").addEventListener("click", () => {
    for (let r = 0; r < ROWS; r += 1) {
      for (let c = 0; c < COLS; c += 1) {
        if (solution[r][c] === "#") continue;
        if (!entries[r][c]) continue;
        marks[r][c] = entries[r][c] === solution[r][c] ? "" : "incorrect";
      }
    }
    messageEl.textContent = "Checked filled cells.";
    closeSettingsMenu();
    render();
    finalizeIfSolved();
  });

  document.getElementById("revealPuzzle").addEventListener("click", () => {
    const confirmed = window.confirm("Are you sure you want to reveal the full board?");
    if (!confirmed) {
      closeSettingsMenu();
      return;
    }

    for (let r = 0; r < ROWS; r += 1) {
      for (let c = 0; c < COLS; c += 1) {
        if (solution[r][c] !== "#") {
          entries[r][c] = solution[r][c];
          marks[r][c] = "revealed";
        }
      }
    }
    messageEl.textContent = "Puzzle revealed.";
    closeSettingsMenu();
    render();
    finalizeIfSolved();
  });

  document.getElementById("clearPuzzle").addEventListener("click", () => {
    for (let r = 0; r < ROWS; r += 1) {
      for (let c = 0; c < COLS; c += 1) {
        if (solution[r][c] !== "#") {
          entries[r][c] = "";
          marks[r][c] = "";
        }
      }
    }
    messageEl.textContent = "Cleared.";
    hasCelebrated = false;
    timerEl.classList.remove("solved");
    closeSettingsMenu();
    render();
  });

  window.addEventListener("keydown", (event) => {
    if (!active) return;

    if (event.key === "Backspace") {
      handleBackspace();
      event.preventDefault();
      return;
    }

    if (event.key === "ArrowRight") {
      direction = "across";
      move(1, "across");
      event.preventDefault();
      render();
      return;
    }
    if (event.key === "ArrowLeft") {
      direction = "across";
      move(-1, "across");
      event.preventDefault();
      render();
      return;
    }
    if (event.key === "ArrowDown") {
      direction = "down";
      move(1, "down");
      event.preventDefault();
      render();
      return;
    }
    if (event.key === "ArrowUp") {
      direction = "down";
      move(-1, "down");
      event.preventDefault();
      render();
      return;
    }

    if (/^[a-zA-Z]$/.test(event.key)) {
      handleLetter(event.key.toUpperCase());
      event.preventDefault();
    }
  });

  document.addEventListener("click", (event) => {
    if (!settingsMenuEl?.open) return;
    if (!settingsMenuEl.contains(event.target)) {
      closeSettingsMenu();
    }
  });

  boardEl.addEventListener("click", (event) => {
    const target = event.target.closest(".cell");
    if (!target || target.classList.contains("block")) return;
    const row = Number(target.dataset.row);
    const col = Number(target.dataset.col);
    if (active && active.row === row && active.col === col) {
      toggleClueDirection();
      return;
    }
    active = { row, col };
    render();
  });

  prevClueEl.addEventListener("click", () => {
    cycleClue(-1);
  });

  nextClueEl.addEventListener("click", () => {
    cycleClue(1);
  });

  activeClueEl.addEventListener("click", () => {
    toggleClueDirection();
  });
}

function initializeBoard() {
  boardEl.style.setProperty("--rows", String(ROWS));
  boardEl.style.setProperty("--cols", String(COLS));

  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      const cell = document.createElement("button");
      cell.className = "cell";
      cell.setAttribute("aria-label", `Row ${r + 1} Column ${c + 1}`);
      cell.dataset.row = String(r);
      cell.dataset.col = String(c);

      if (solution[r][c] === "#") {
        cell.classList.add("block");
        cell.disabled = true;
        boardEl.appendChild(cell);
        continue;
      }

      const number = numbering[`${r},${c}`];
      if (number) {
        const numberEl = document.createElement("span");
        numberEl.className = "number";
        numberEl.textContent = String(number);
        cell.appendChild(numberEl);
      }

      const letterEl = document.createElement("span");
      letterEl.className = "letter";
      cell.appendChild(letterEl);

      cellEls[r][c] = cell;
      letterEls[r][c] = letterEl;
      boardEl.appendChild(cell);
    }
  }
}

function buildKeyboard() {
  const rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"];
  keyboardEl.innerHTML = "";

  rows.forEach((rowLetters) => {
    const rowEl = document.createElement("div");
    rowEl.className = "keyboard-row";
    rowEl.style.gridTemplateColumns = `repeat(${rowLetters.length}, minmax(0, 1fr))`;

    rowLetters.split("").forEach((ch) => {
      const key = document.createElement("button");
      key.className = "key";
      key.textContent = ch;
      key.setAttribute("aria-label", `Type ${ch}`);
      key.addEventListener("click", () => handleLetter(ch));
      rowEl.appendChild(key);
    });

    keyboardEl.appendChild(rowEl);
  });

  const actionRow = document.createElement("div");
  actionRow.className = "keyboard-row actions";

  const backspaceKey = document.createElement("button");
  backspaceKey.className = "key key-wide";
  backspaceKey.textContent = "Delete";
  backspaceKey.addEventListener("click", handleBackspace);

  actionRow.appendChild(backspaceKey);
  keyboardEl.appendChild(actionRow);
}

function handleLetter(letter) {
  if (!active) return;
  const clueNumberBefore = getClueNumberForCell(active, direction);
  entries[active.row][active.col] = letter;
  marks[active.row][active.col] = "";

  if (clueNumberBefore && isClueFilled(clueNumberBefore, direction)) {
    const moved = jumpToNextUnfilledClue(direction, clueNumberBefore);
    if (!moved) {
      const otherDirection = direction === "across" ? "down" : "across";
      const switched = jumpToFirstUnfilledClue(otherDirection);
      if (!switched) {
        moveToNextUnfilledCell(1);
      }
    }
  } else {
    moveToNextUnfilledCell(1);
  }

  messageEl.textContent = "";
  render();

  if (isSolved()) {
    finalizeIfSolved();
  }
}

function handleBackspace() {
  if (!active) return;

  const { row, col } = active;
  if (entries[row][col]) {
    entries[row][col] = "";
    marks[row][col] = "";
  } else {
    move(-1);
    if (active) {
      entries[active.row][active.col] = "";
      marks[active.row][active.col] = "";
    }
  }

  messageEl.textContent = "";
  render();
}

function toggleDirection() {
  direction = direction === "across" ? "down" : "across";
  render();
}

function closeSettingsMenu() {
  if (settingsMenuEl?.open) {
    settingsMenuEl.open = false;
  }
}

function render() {
  directionBadgeEl.textContent = capitalize(direction);
  const activeCells = getActiveCells(active, direction);
  const activeSet = new Set(activeCells.map((pos) => `${pos.row},${pos.col}`));
  const startCell = activeCells[0];
  activeClueNumber = startCell ? numbering[`${startCell.row},${startCell.col}`] ?? null : null;

  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      if (solution[r][c] === "#") {
        continue;
      }
      const cell = cellEls[r][c];
      const letterEl = letterEls[r][c];
      letterEl.textContent = entries[r][c];
      cell.classList.remove("incorrect", "revealed", "selected", "focused-word");
      if (marks[r][c] === "incorrect") cell.classList.add("incorrect");
      if (marks[r][c] === "revealed") cell.classList.add("revealed");
      if (active && active.row === r && active.col === c) cell.classList.add("selected");
      if (activeSet.has(`${r},${c}`)) cell.classList.add("focused-word");
    }
  }

  if (activeClueNumber && puzzle.clues[direction][activeClueNumber]) {
    activeClueEl.textContent = `${activeClueNumber} ${capitalize(direction)}: ${puzzle.clues[direction][activeClueNumber]}`;
    activeClueEl.disabled = false;
  } else {
    activeClueEl.textContent = "Tap a square to begin.";
    activeClueEl.disabled = true;
  }
}

function getClueNumbers(dir) {
  return Object.keys(puzzle.clues[dir] || {})
    .map(Number)
    .sort((a, b) => a - b);
}

function jumpToClue(number, dir) {
  const start = clueStarts[dir]?.[number];
  if (!start) return false;
  direction = dir;
  active = { row: start.row, col: start.col };
  render();
  return true;
}

function getClueNumberForCell(cell, dir) {
  if (!cell) return null;
  const cells = getActiveCells(cell, dir);
  const start = cells[0];
  if (!start) return null;
  return numbering[`${start.row},${start.col}`] ?? null;
}

function isClueFilled(number, dir) {
  const start = clueStarts[dir]?.[number];
  if (!start) return false;
  const delta = dir === "across" ? [0, 1] : [1, 0];
  let r = start.row;
  let c = start.col;

  while (r >= 0 && r < ROWS && c >= 0 && c < COLS && solution[r][c] !== "#") {
    if (!entries[r][c]) return false;
    r += delta[0];
    c += delta[1];
  }
  return true;
}

function getUnfilledClueNumbers(dir) {
  return getClueNumbers(dir).filter((num) => !isClueFilled(num, dir));
}

function jumpToNextUnfilledClue(dir, currentNumber) {
  const numbers = getUnfilledClueNumbers(dir);
  if (!numbers.length) return false;
  const currentIndex = numbers.indexOf(currentNumber);
  const nextIndex = currentIndex === -1 ? 0 : (currentIndex + 1) % numbers.length;
  return jumpToClue(numbers[nextIndex], dir);
}

function jumpToFirstUnfilledClue(dir) {
  const numbers = getUnfilledClueNumbers(dir);
  if (!numbers.length) return false;
  return jumpToClue(numbers[0], dir);
}

function cycleClue(step) {
  const numbers = getClueNumbers(direction);
  if (!numbers.length) return;

  let index = numbers.indexOf(activeClueNumber);
  if (index === -1) {
    index = step > 0 ? -1 : 0;
  }
  const nextIndex = (index + step + numbers.length) % numbers.length;
  jumpToClue(numbers[nextIndex], direction);
}

function toggleClueDirection() {
  const nextDirection = direction === "across" ? "down" : "across";
  const crossing = findNearestAttachedClueStart(nextDirection);
  if (!crossing) {
    render();
    return;
  }

  direction = nextDirection;
  active = { row: crossing.row, col: crossing.col };
  render();
}

function findNearestAttachedClueStart(nextDirection) {
  if (!active) return null;
  const currentCells = getActiveCells(active, direction);
  if (!currentCells.length) return null;

  let activeIndex = currentCells.findIndex((cell) => cell.row === active.row && cell.col === active.col);
  if (activeIndex < 0) activeIndex = 0;

  const orderedCells = currentCells
    .map((cell, index) => ({ cell, distance: Math.abs(index - activeIndex) }))
    .sort((a, b) => a.distance - b.distance)
    .map((item) => item.cell);

  for (const cell of orderedCells) {
    const oppositeCells = getActiveCells(cell, nextDirection);
    if (oppositeCells.length <= 1) continue;
    const start = oppositeCells[0];
    const num = numbering[`${start.row},${start.col}`];
    if (!num) continue;
    if (!puzzle.clues[nextDirection][num]) continue;
    return start;
  }

  return null;
}

function findFirstOpenCell() {
  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      if (solution[r][c] !== "#") return { row: r, col: c };
    }
  }
  return null;
}

function move(step, forcedDirection = direction) {
  if (!active) return;
  const delta = forcedDirection === "across" ? [0, step] : [step, 0];

  let r = active.row + delta[0];
  let c = active.col + delta[1];

  while (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
    if (solution[r][c] !== "#") {
      active = { row: r, col: c };
      return;
    }
    r += delta[0];
    c += delta[1];
  }
}

function moveToNextUnfilledCell(step, forcedDirection = direction) {
  if (!active) return;
  const delta = forcedDirection === "across" ? [0, step] : [step, 0];

  let r = active.row + delta[0];
  let c = active.col + delta[1];

  while (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
    if (solution[r][c] !== "#" && entries[r][c] === "") {
      active = { row: r, col: c };
      return;
    }
    r += delta[0];
    c += delta[1];
  }
}

function getActiveCells(cell, dir) {
  if (!cell) return [];
  if (solution[cell.row][cell.col] === "#") return [];

  const result = [];
  const delta = dir === "across" ? [0, 1] : [1, 0];

  let r = cell.row;
  let c = cell.col;
  while (r - delta[0] >= 0 && c - delta[1] >= 0 && solution[r - delta[0]][c - delta[1]] !== "#") {
    r -= delta[0];
    c -= delta[1];
  }

  while (r < ROWS && c < COLS && solution[r][c] !== "#") {
    result.push({ row: r, col: c });
    r += delta[0];
    c += delta[1];
  }

  return result;
}

function buildNumbering(grid) {
  const map = {};
  let count = 1;

  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      if (grid[r][c] === "#") continue;

      const startsAcross = (c === 0 || grid[r][c - 1] === "#") && c + 1 < COLS && grid[r][c + 1] !== "#";
      const startsDown = (r === 0 || grid[r - 1][c] === "#") && r + 1 < ROWS && grid[r + 1][c] !== "#";

      if (startsAcross || startsDown) {
        map[`${r},${c}`] = count;
        count += 1;
      }
    }
  }

  return map;
}

function buildClueStarts(grid, numbers) {
  const starts = { across: {}, down: {} };

  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      if (grid[r][c] === "#") continue;
      const number = numbers[`${r},${c}`];
      if (!number) continue;

      const startsAcross = (c === 0 || grid[r][c - 1] === "#") && c + 1 < COLS && grid[r][c + 1] !== "#";
      const startsDown = (r === 0 || grid[r - 1][c] === "#") && r + 1 < ROWS && grid[r + 1][c] !== "#";

      if (startsAcross && puzzle.clues.across[number]) {
        starts.across[number] = { row: r, col: c };
      }
      if (startsDown && puzzle.clues.down[number]) {
        starts.down[number] = { row: r, col: c };
      }
    }
  }

  return starts;
}

function setInitialSelection() {
  if (clueStarts.across[1]) {
    direction = "across";
    active = { ...clueStarts.across[1] };
    return;
  }
  if (clueStarts.down[1]) {
    direction = "down";
    active = { ...clueStarts.down[1] };
  }
}

function isSolved() {
  for (let r = 0; r < ROWS; r += 1) {
    for (let c = 0; c < COLS; c += 1) {
      if (solution[r][c] === "#") continue;
      if (entries[r][c] !== solution[r][c]) return false;
    }
  }
  return true;
}

function finalizeIfSolved() {
  if (!isSolved()) return;
  stopTimer();
  timerEl.classList.add("solved");
  if (!hasCelebrated) {
    launchConfetti();
    hasCelebrated = true;
  }
  messageEl.textContent = "Done. Happy Valentine's Day.";
}

function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function startTimer() {
  if (timerId) return;
  timerId = setInterval(() => {
    seconds += 1;
    const min = String(Math.floor(seconds / 60)).padStart(2, "0");
    const sec = String(seconds % 60).padStart(2, "0");
    timerEl.textContent = `${min}:${sec}`;
  }, 1000);
}

function stopTimer() {
  if (!timerId) return;
  clearInterval(timerId);
  timerId = null;
}

function launchConfetti() {
  const canvas = document.createElement("canvas");
  canvas.className = "confetti-canvas";
  document.body.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    canvas.remove();
    return;
  }

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };
  resize();

  const colors = ["#f05a7e", "#ffb347", "#4fc3f7", "#7ed957", "#ffd700", "#ff6f61"];
  const pieces = Array.from({ length: 140 }, () => ({
    x: Math.random() * canvas.width,
    y: -20 - Math.random() * canvas.height * 0.4,
    w: 6 + Math.random() * 8,
    h: 8 + Math.random() * 10,
    vy: 2 + Math.random() * 3,
    vx: -1.8 + Math.random() * 3.6,
    rot: Math.random() * Math.PI * 2,
    spin: -0.15 + Math.random() * 0.3,
    color: colors[Math.floor(Math.random() * colors.length)]
  }));

  const start = performance.now();
  const duration = 2800;

  function frame(now) {
    const elapsed = now - start;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    pieces.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.015;
      p.rot += p.spin;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
      ctx.restore();
    });

    if (elapsed < duration) {
      requestAnimationFrame(frame);
    } else {
      canvas.remove();
    }
  }

  requestAnimationFrame(frame);
}
