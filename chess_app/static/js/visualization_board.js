const PIECE_IMAGE_MAP = {
    P: 'wP', N: 'wN', B: 'wB', R: 'wR', Q: 'wQ', K: 'wK',
    p: 'bP', n: 'bN', b: 'bB', r: 'bR', q: 'bQ', k: 'bK'
};

function getPieceSet() {
  return window.PIECE_SET || 'merida';
}

let currentFen = window.INITIAL_FEN || 'start';
let orientation = 'white';
let draggedFrom = null;
let draggedPiece = null;
let navigationFens = [currentFen];
let navigationSans = [];
let navigationIndex = 0;
let selectedSourceSquare = null;
let userHasAnswered = false;
let solutionShown = false;
let historyMoves = [];
let historyItems = [];

function getItemText(item) {
  if (typeof item === "object" && item !== null) {
    return item.text || '';
  }
  return item || '';
}

function parseFenBoard(fen) {
    const placement = (fen || '').split(' ')[0];
    const rows = placement.split('/');
    if (rows.length !== 8) {
        return Array.from({ length: 8 }, () => Array(8).fill(null));
    }
    return rows.map(row => {
        const cells = [];
        for (const ch of row) {
            if (/\d/.test(ch)) {
                for (let i = 0; i < Number(ch); i += 1) cells.push(null);
            } else {
                cells.push(ch);
            }
        }
        return cells;
    });
}

function setOrientationFromFen(fen) {
  const parts = (fen || '').split(' ');
  const sideToMove = parts.length > 1 ? parts[1] : 'w';
  orientation = sideToMove === 'b' ? 'black' : 'white';
}

function coordsToSquare(row, col) {
    const file = 'abcdefgh'[col];
    const rank = String(8 - row);
    return `${file}${rank}`;
}

function displayOrder() {
    const rows = [...Array(8).keys()];
    const cols = [...Array(8).keys()];
    if (orientation === 'black') {
        rows.reverse();
        cols.reverse();
    }
    return { rows, cols };
}

function updateStatus(message) {
    const el = document.getElementById('status');
    if (el) el.textContent = message || '';
}

function updateHistory(text, items = null) {
  if (Array.isArray(items)) {
    historyItems = items;
  } else {
    historyItems = [];
  }
  renderHistoryHighlight(text || '');
}

function renderHistoryHighlight(fallbackText = '') {
  const el = document.getElementById('moveHistory');
  if (!el) return;

  el.innerHTML = '';

  if (!historyItems.length) {
    el.textContent = fallbackText;
    return;
  }

  let moveIndex = 0;

  historyItems.forEach((item) => {
    const span = document.createElement('span');

    if (typeof item === "object" && item !== null && item.type === "marker") {
      span.textContent = item.text + ' ';
      span.classList.add('solution-marker');
      el.appendChild(span);
      return;
    }

    span.textContent = getItemText(item) + ' ';

    // navigationIndex 0 = Startstellung
    // erster Zug = moveIndex 0
    if (moveIndex === navigationIndex - 1) {
      span.classList.add('current-move');
    }

    moveIndex++;
    el.appendChild(span);
  });
}

function updateNavigationStatus() {
    const statusEl = document.getElementById('navStatus');
    if (statusEl) {
        const totalMoves = Math.max(0, navigationFens.length - 1);
        statusEl.textContent = `Zug ${navigationIndex} / ${totalMoves}`;
    }

    const prevBtn = document.getElementById('prevMoveBtn');
    const nextBtn = document.getElementById('nextMoveBtn');
    if (prevBtn) prevBtn.disabled = !solutionShown || navigationIndex <= 0;
    if (nextBtn) nextBtn.disabled = !solutionShown || navigationIndex >= navigationFens.length - 1;
}

function setNavigationLine(fens, sans, index = 0) {
    if (!Array.isArray(fens) || fens.length === 0) {
        navigationFens = [currentFen];
        navigationSans = [];
        navigationIndex = 0;
    } else {
        navigationFens = [...fens];
        navigationSans = Array.isArray(sans) ? [...sans] : [];
        navigationIndex = Math.max(0, Math.min(index, navigationFens.length - 1));
        currentFen = navigationFens[navigationIndex];
    }
    renderBoard();
    updateNavigationStatus();
    renderHistoryHighlight();
}

function appendNavigationFen(fen) {
    if (navigationIndex < navigationFens.length - 1) {
        navigationFens = navigationFens.slice(0, navigationIndex + 1);
        navigationSans = navigationSans.slice(0, navigationIndex);
    }
    navigationFens.push(fen);
    navigationIndex = navigationFens.length - 1;
    currentFen = fen;
    updateNavigationStatus();
}

function renderBoard() {
    const boardEl = document.getElementById('board');
    if (!boardEl) return;
    boardEl.innerHTML = '';

    const state = parseFenBoard(currentFen);
    const { rows, cols } = displayOrder();

    rows.forEach(row => {
        cols.forEach(col => {
            const squareName = coordsToSquare(row, col);
            const squareEl = document.createElement('div');
            // Koordinaten berechnen
            const fileChar = squareName[0];
            const rankChar = squareName[1];


            squareEl.className = `square ${(row + col) % 2 === 0 ? 'light' : 'dark'}`;
            squareEl.dataset.square = squareName;
            squareEl.addEventListener('click', () => {
              if (!selectedSourceSquare) {
                selectSourceSquare(squareEl, squareName);
                return;
              }
              if (selectedSourceSquare === squareName) {
                clearSelectedSquare();
                updateStatus('Auswahl aufgehoben.');
                return;
              }
              const move = selectedSourceSquare + squareName;
              clearSelectedSquare();
              checkSolutionMove(move);
            });


            squareEl.addEventListener('dragover', event => event.preventDefault());
            squareEl.addEventListener('drop', event => {
                event.preventDefault();
                const from = event.dataTransfer.getData('text/plain') || draggedFrom;
                const to = squareName;
                clearHighlights();
                if (from && to) sendMove(`${from}${to}`);
                draggedFrom = null;
                draggedPiece = null;
            });
            squareEl.addEventListener('dragenter', () => squareEl.classList.add('highlight'));
            squareEl.addEventListener('dragleave', () => squareEl.classList.remove('highlight'));

            const piece = state[row][col];
            if (piece) {
                const pieceEl = document.createElement('img');
                pieceEl.className = `piece ${piece === piece.toUpperCase() ? 'white' : 'black'}`;
                pieceEl.src = `/static/img/chesspieces/${getPieceSet()}/${PIECE_IMAGE_MAP[piece]}.svg`;
                pieceEl.alt = piece;
                pieceEl.draggable = true;
                pieceEl.dataset.square = squareName;
                pieceEl.addEventListener('dragstart', event => {
                    draggedFrom = squareName;
                    draggedPiece = piece;
                    event.dataTransfer.setData('text/plain', squareName);
                    pieceEl.classList.add('dragging');
                });
                pieceEl.addEventListener('dragend', () => {
                    pieceEl.classList.remove('dragging');
                    clearHighlights();
                });
                squareEl.appendChild(pieceEl);
            }

            boardEl.appendChild(squareEl);
        });
    });
    renderOuterCoordinates();
}

function renderOuterCoordinates() {
  const topFilesEl = document.getElementById('boardTopFiles');
  const bottomFilesEl = document.getElementById('boardBottomFiles');
  const leftRanksEl = document.getElementById('boardRanksLeft');
  const rightRanksEl = document.getElementById('boardRanksRight');

  if (!topFilesEl || !bottomFilesEl || !leftRanksEl || !rightRanksEl) return;

  topFilesEl.innerHTML = '';
  bottomFilesEl.innerHTML = '';
  leftRanksEl.innerHTML = '';
  rightRanksEl.innerHTML = '';

  const files = orientation === 'white'
    ? ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    : ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'];

  const ranks = orientation === 'white'
    ? ['8', '7', '6', '5', '4', '3', '2', '1']
    : ['1', '2', '3', '4', '5', '6', '7', '8'];

  files.forEach(file => {
    const top = document.createElement('div');
    top.className = 'coord-outer';
    top.textContent = file;
    topFilesEl.appendChild(top);

    const bottom = document.createElement('div');
    bottom.className = 'coord-outer';
    bottom.textContent = file;
    bottomFilesEl.appendChild(bottom);
  });

  ranks.forEach(rank => {
    const left = document.createElement('div');
    left.className = 'coord-outer';
    left.textContent = rank;
    leftRanksEl.appendChild(left);

    const right = document.createElement('div');
    right.className = 'coord-outer';
    right.textContent = rank;
    rightRanksEl.appendChild(right);
  });
}

function clearHighlights() {
    document.querySelectorAll('.square.highlight').forEach(el => el.classList.remove('highlight'));
}

function setFenLocally(fen) {
    currentFen = fen;
    renderBoard();
    updateNavigationStatus();
}

function goToPreviousMove() {
    if (!userHasAnswered) {
      updateStatus('Bitte zuerst einen Lösungszug eingeben.');
      return;
    }
    if (navigationIndex <= 0) return;
    navigationIndex -= 1;
    currentFen = navigationFens[navigationIndex];
    renderBoard();
    updateNavigationStatus();
    renderHistoryHighlight();
} 

function goToNextMove() {
    if (!userHasAnswered) {
      updateStatus('Bitte zuerst einen Lösungszug eingeben.');
      return;
    }
    if (navigationIndex >= navigationFens.length - 1) return;
    navigationIndex += 1;
    currentFen = navigationFens[navigationIndex];
    renderBoard();
    updateNavigationStatus();
    renderHistoryHighlight();
}

async function sendMove(moveText = null) {
    const moveInput = document.getElementById('moveInput');
    const move = (moveText || moveInput?.value || '').trim();
    if (!move) {
        updateStatus('Bitte einen Zug eingeben.');
        return;
    }

    try {
        const response = await fetch('/visualisierung/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move })
        });
        const data = await response.json();
        if (data.ok) {
            appendNavigationFen(data.fen);
            setFenLocally(data.fen);
            if (moveInput && !moveText) moveInput.value = '';
        }
        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Ausführen des Zugs.');
    }
}

async function resetBoard() {
    try {
        const response = await fetch('/visualisierung/reset', { method: 'POST' });
        const data = await response.json();
        if (data.ok) {
            setNavigationLine(data.navigation_fens || [data.fen], data.navigation_sans || [], 0);
            updateHistory(data.history, data.history_items);
        }
        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Zurücksetzen.');
    }
}

function flipBoard() {
    orientation = orientation === 'white' ? 'black' : 'white';
    renderBoard();
}

async function setFen() {
    const fenInput = document.getElementById('fenInput');
    const fen = (fenInput?.value || '').trim();
    if (!fen) {
        updateStatus('Bitte eine FEN eingeben.');
        return;
    }

    try {
        const response = await fetch('/visualisierung/set_fen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fen })
        });
        const data = await response.json();
        if (data.ok) {
            setNavigationLine([data.fen], [], 0);
        }
        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Laden der FEN.');
    }
}

function generateTask() {
  const number1 = parseInt(document.getElementById('number1')?.value || '0', 10);
  const number2 = parseInt(document.getElementById('number2')?.value || '0', 10);
  const select1 = document.getElementById('select1')?.value || '';
  const select2 = document.getElementById('select2')?.value || '';

  fetch('/visualisierung/generate_task', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      number1: number1,
      number2: number2,
      select1: select1,
      select2: select2
    })
  })
    .then(response => response.json())
    .then(data => {
      console.log("Antwort von /generate_task:", data);

      if (data.ok) {
        userHasAnswered = false;
        solutionShown = false;
        setOrientationFromFen(data.fen);
        setNavigationLine(data.navigation_fens || [data.fen], data.navigation_sans || [], 0);
        updateHistory(data.history, data.history_items);
      }

      updateStatus(data.message);
    })
    .catch(error => {
      console.error(error);
      updateStatus('Fehler beim Generieren der Aufgabe');
    });
}

/*function generateTask() {
  const number1 = parseInt(document.getElementById('number1')?.value || '0', 10);
  const number2 = parseInt(document.getElementById('number2')?.value || '0', 10);
  const select1 = document.getElementById('select1')?.value || '';
  const select2 = document.getElementById('select2')?.value || '';

  fetch('/visualisierung/generate_task', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      number1: number1,
      number2: number2,
      select1: select1,
      select2: select2
    })
  })
    .then(response => response.json())
    .then(data => {
      console.log("Antwort von /generate_task:", data);
      if (data.ok) {
        board.position(data.fen);
        updateHistory(data.history);
      }
      updateStatus(data.message);
    })
    .catch(() => {
      updateStatus('Fehler beim Generieren der Aufgabe');
    });
}*/

/*
async function generateTask() {
    try {
        const response = await fetch('/visualisierung/generate_task', { method: 'POST' });
        const data = await response.json();
        if (data.ok) {
            setNavigationLine(data.navigation_fens || [data.fen], data.navigation_sans || [], 0);
            updateHistory(data.history);
        }
        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Generieren der Aufgabe.');
    }
}
*/

async function showSolution() {
    try {
        const response = await fetch('/visualisierung/solution');
        const data = await response.json();
        if (data.ok) {
            solutionShown = true; 
            updateHistory(data.history, data.history_items);
            setNavigationLine(data.navigation_fens || navigationFens, data.navigation_sans || navigationSans, navigationIndex);
        }
        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Laden der Lösung.');
    }
}

async function downloadPgn() {
  try {
    const response = await fetch('/visualisierung/download_pgn');

    if (!response.ok) {
      // Fehler vom Server holen
      let message = "Fehler beim Download";
      try {
        const data = await response.json();
        message = data.message || message;
      } catch {
        // fallback
      }
      alert(message);
      return;
    }

    // Datei als Blob holen
    const blob = await response.blob();

    // Dateiname aus Header lesen (optional)
    let filename = "aufgabe.pgn";
    const disposition = response.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename")) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match) filename = match[1];
    }

    // Download auslösen
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

  } catch (error) {
    alert("Netzwerkfehler beim Download");
  }
}
function bindEvents() {
    document.getElementById('moveBtn')?.addEventListener('click', () => sendMove());
    document.getElementById('resetBtn')?.addEventListener('click', resetBoard);
    document.getElementById('flipBtn')?.addEventListener('click', flipBoard);
    document.getElementById('fenBtn')?.addEventListener('click', setFen);
    document.getElementById('generateTaskBtn')?.addEventListener('click', generateTask);
    document.getElementById('showSolutionBtn')?.addEventListener('click', showSolution);
    document.getElementById('prevMoveBtn')?.addEventListener('click', goToPreviousMove);
    document.getElementById('nextMoveBtn')?.addEventListener('click', goToNextMove);
    document.getElementById('moveInput')?.addEventListener('keydown', event => {
        if (event.key === 'Enter') sendMove();
    });
    document.getElementById('fenInput')?.addEventListener('keydown', event => {
        if (event.key === 'Enter') setFen();
    });
    document.getElementById('downloadPgnBtn')?.addEventListener('click', downloadPgn);
}

document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    setNavigationLine([currentFen], [], 0);
});

function clearSelectedSquare() {
  selectedSourceSquare = null;
  document.querySelectorAll('.square.selected')
      .forEach(el => el.classList.remove('selected'));
}

function selectSourceSquare(squareEl, squareName) {
    clearSelectedSquare();
    selectedSourceSquare = squareName;
    squareEl.classList.add('selected');
}

async function checkSolutionMove(move) {
    try {
        const response = await fetch('/visualisierung/check_solution_move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move })
        });

        const data = await response.json();

        if (data.ok) {
          userHasAnswered = true;
          updateNavigationStatus();
        }

        updateStatus(data.message);

        if (data.correct) {
            clearSelectedSquare();
        }
    } catch {
        updateStatus('Fehler beim Prüfen der Lösung.');
    }
}

window.setBoardFen = function (fen) {
  currentFen = fen;
  setOrientationFromFen(fen);
  setNavigationLine([fen], [], 0);
};

window.renderBoard = renderBoard;

window.setBoardFen = function (fen) {
  currentFen = fen;
  setOrientationFromFen(fen);
  setNavigationLine([fen], [], 0);
};