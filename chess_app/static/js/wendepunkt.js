let navigationFens = [window.INITIAL_FEN || 'start'];
let navigationSans = [];
let navigationIndex = 0;
let selectedSourceSquare = null;
let solutionShown = false;
let historyItems = [];
let solutionItems = [];
let userHasAnswered = false;

function renderHistoryHighlight() {
  const el = document.getElementById("moveHistory");
  if (!el) return;

  const items =
    solutionShown && solutionItems.length
      ? solutionItems
      : historyItems;

  el.innerHTML = "";

  let mainMoveIndex = 0;

  items.forEach((item) => {
    const span = document.createElement("span");

    const isObject =
      typeof item === "object" && item !== null;

    const isMarker =
      isObject && item.type === "marker";

    const isVariation =
      isObject && item.type === "variation";

    const text =
      isObject
        ? item.text
        : item;

    span.textContent = text + " ";

    if (isMarker || isVariation) {
      span.classList.add("solution-marker");
      el.appendChild(span);
      return;
    }

    if (mainMoveIndex === navigationIndex - 1) {
      span.classList.add("current-move");
    }

    mainMoveIndex += 1;

    el.appendChild(span);
  });
}

function boardInteractionOptions() {
    return {
        onSquareClick: handleSquareClick,
        onMove: checkMove,
        enableDrag: true,
    };
}

function updateStatus(message) {
    const el = document.getElementById('status');
    if (el) el.textContent = message || '';
}

function updateNavigationStatus() {
    const statusEl = document.getElementById('navStatus');

    if (statusEl) {
        statusEl.textContent =
            `Zug ${navigationIndex} / ${Math.max(0, navigationFens.length - 1)}`;
    }

    const prevBtn = document.getElementById('prevMoveBtn');
    const nextBtn = document.getElementById('nextMoveBtn');

    if (prevBtn) prevBtn.disabled = navigationIndex <= 0;
    if (nextBtn) nextBtn.disabled = navigationIndex >= navigationFens.length - 1;
}

function setNavigationLine(fens, sans, index = 0) {
    navigationFens = Array.isArray(fens) && fens.length ? [...fens] : [window.Board.getFen()];
    navigationSans = Array.isArray(sans) ? [...sans] : [];
    navigationIndex = Math.max(0, Math.min(index, navigationFens.length - 1));

    window.Board.setFenAndOrientation(
        navigationFens[navigationIndex],
        boardInteractionOptions()
    );

    updateNavigationStatus();
}

function goToPreviousMove() {
    if (navigationIndex <= 0) return;

    navigationIndex -= 1;

    window.Board.setFen(
        navigationFens[navigationIndex],
        boardInteractionOptions()
    );

  updateNavigationStatus();
  renderHistoryHighlight();
}

function goToNextMove() {
    if (navigationIndex >= navigationFens.length - 1) return;

    navigationIndex += 1;

    window.Board.setFen(
        navigationFens[navigationIndex],
        boardInteractionOptions()
    );

    updateNavigationStatus();
    renderHistoryHighlight();
}

function clearSelectedSquare() {
    selectedSourceSquare = null;

    document
        .querySelectorAll('.square.selected')
        .forEach(el => el.classList.remove('selected'));
}

function selectSourceSquare(squareEl, squareName) {
    clearSelectedSquare();
    selectedSourceSquare = squareName;
    squareEl.classList.add('selected');
}

function handleSquareClick(squareEl, squareName) {
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
    checkMove(move);
}

function updateTaskId(taskId) {
  const el = document.getElementById("taskIdDisplay");

  if (el) {
    el.textContent = taskId || "-";
  }
}

async function checkMove(move) {
  const response = await fetch('/wendepunkt/check_move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      move: move,
      index: navigationIndex,
    }),
  });

  const data = await response.json();

  if (data.ok) {
    userHasAnswered = true;

    document.getElementById("showSolutionBtn").disabled = false;
    document.getElementById("downloadPgnBtn").disabled = false;
  }

  updateStatus(data.message);
}

async function generateTask() {
    let rating = parseInt(
      document.getElementById('ratingInput')?.value || '2000',
      10
    );

    if (isNaN(rating)) {
      rating = 2000;
    }

    rating = Math.max(1000, Math.min(3000, rating));
    rating = Math.round(rating / 100) * 100;

    const response = await fetch('/wendepunkt/generate_task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating }),
    });

    const data = await response.json();

    if (!data.ok) {
        updateStatus(data.message);
        return;
    }

    setNavigationLine(
        data.navigation_fens || [data.fen],
        data.navigation_sans || [],
        0
    );

    userHasAnswered = false;
    solutionShown = false;
    historyItems = data.history_items || [];
    solutionItems = [];
    updateTaskId(data.task_id);
    renderHistoryHighlight();

    document.getElementById("showSolutionBtn").disabled = true;
    document.getElementById("downloadPgnBtn").disabled = true;

    const historyEl = document.getElementById('moveHistory');

    if (historyEl) {
      historyItems = data.history_items || [];

      renderHistoryHighlight();
    }

    updateStatus(data.message);
}

function bindEvents() {
    document
        .getElementById('generateTaskBtn')
        ?.addEventListener('click', generateTask);

    document
        .getElementById('prevMoveBtn')
        ?.addEventListener('click', goToPreviousMove);

    document
        .getElementById('nextMoveBtn')
        ?.addEventListener('click', goToNextMove);

    document
      .getElementById("showSolutionBtn")
      ?.addEventListener("click", showSolution);

    document
      .getElementById("downloadPgnBtn")
      ?.addEventListener("click", downloadPgn);
}

document.addEventListener('DOMContentLoaded', () => {
  bindEvents();

  if (window.INITIAL_TASK) {
    navigationFens =
      window.INITIAL_TASK.navigation_fens || [window.INITIAL_TASK.fen];

    navigationSans =
      window.INITIAL_TASK.navigation_sans || [];

    navigationIndex = 0;

    historyItems =
      window.INITIAL_TASK.history_items || [];

    solutionShown = false;
    solutionItems = [];

    window.Board.setFenAndOrientation(
      navigationFens[0],
      boardInteractionOptions()
    );

    renderHistoryHighlight();
    updateNavigationStatus();
    updateTaskId(window.INITIAL_TASK.task_id);

    return;
  }

  window.Board.setFenAndOrientation(
    window.INITIAL_FEN || 'start',
    boardInteractionOptions()
  );

  setNavigationLine([window.Board.getFen()], [], 0);
});

async function showSolution() {
  const response = await fetch("/wendepunkt/solution");
  const data = await response.json();

  if (!response.ok || !data.ok) {
    updateStatus(data.message || "Lösung konnte nicht geladen werden.");
    return;
  }

  solutionShown = true;
  solutionItems = data.history_items || [];

  renderHistoryHighlight();
  updateStatus(data.message);
}

async function downloadPgn() {
  const response = await fetch("/wendepunkt/download_pgn");

  if (!response.ok) {
    const data = await response.json();
    updateStatus(data.message || "PGN konnte nicht heruntergeladen werden.");
    return;
  }

  const blob = await response.blob();

  let filename = "wendepunkt.pgn";
  const disposition = response.headers.get("Content-Disposition");

  if (disposition && disposition.includes("filename")) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match) filename = match[1];
  }

  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url;
  a.download = filename;

  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
}