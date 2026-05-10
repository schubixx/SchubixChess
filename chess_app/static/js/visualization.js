let navigationFens = [window.INITIAL_FEN || 'start'];
let navigationSans = [];
let navigationIndex = 0;

let selectedSourceSquare = null;
let userHasAnswered = false;
let solutionShown = false;
let historyItems = [];

function boardInteractionOptions() {
    return {
        onSquareClick: handleSquareClick,
        onMove: checkSolutionMove,
        enableDrag: true,
    };
}

function updateStatus(message) {
    const el = document.getElementById('status');

    if (el) {
        el.textContent = message || '';
    }
}

function getItemText(item) {
    if (typeof item === 'object' && item !== null) {
        return item.text || '';
    }

    return item || '';
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

    if (!el) {
        return;
    }

    el.innerHTML = '';

    if (!historyItems.length) {
        el.textContent = fallbackText;
        return;
    }

    let moveIndex = 0;

    historyItems.forEach(item => {
        const span = document.createElement('span');

        if (typeof item === 'object' && item !== null && item.type === 'marker') {
            span.textContent = `${item.text} `;
            span.classList.add('solution-marker');
            el.appendChild(span);
            return;
        }

        span.textContent = `${getItemText(item)} `;

        if (moveIndex === navigationIndex - 1) {
            span.classList.add('current-move');
        }

        moveIndex += 1;
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

    if (prevBtn) {
        prevBtn.disabled = !solutionShown || navigationIndex <= 0;
    }

    if (nextBtn) {
        nextBtn.disabled = !solutionShown || navigationIndex >= navigationFens.length - 1;
    }
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
    checkSolutionMove(move);
}

function setNavigationLine(fens, sans, index = 0) {
    if (!Array.isArray(fens) || fens.length === 0) {
        navigationFens = [window.Board.getFen()];
        navigationSans = [];
        navigationIndex = 0;
    } else {
        navigationFens = [...fens];
        navigationSans = Array.isArray(sans) ? [...sans] : [];
        navigationIndex = Math.max(0, Math.min(index, navigationFens.length - 1));
    }

    window.Board.setFen(navigationFens[navigationIndex], boardInteractionOptions());
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
    updateNavigationStatus();
}

function setFenLocally(fen) {
    window.Board.setFen(fen, boardInteractionOptions());
    updateNavigationStatus();
}

function goToPreviousMove() {
    if (!userHasAnswered) {
        updateStatus('Bitte zuerst einen Lösungszug eingeben.');
        return;
    }

    if (navigationIndex <= 0) {
        return;
    }

    navigationIndex -= 1;
    window.Board.setFen(navigationFens[navigationIndex], boardInteractionOptions());

    updateNavigationStatus();
    renderHistoryHighlight();
}

function goToNextMove() {
    if (!userHasAnswered) {
        updateStatus('Bitte zuerst einen Lösungszug eingeben.');
        return;
    }

    if (navigationIndex >= navigationFens.length - 1) {
        return;
    }

    navigationIndex += 1;
    window.Board.setFen(navigationFens[navigationIndex], boardInteractionOptions());

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
            body: JSON.stringify({ move }),
        });

        const data = await response.json();

        if (data.ok) {
            appendNavigationFen(data.fen);
            setFenLocally(data.fen);

            if (moveInput && !moveText) {
                moveInput.value = '';
            }
        }

        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Ausführen des Zugs.');
    }
}

async function resetBoard() {
    try {
        const response = await fetch('/visualisierung/reset', {
            method: 'POST',
        });

        const data = await response.json();

        if (data.ok) {
            setNavigationLine(
                data.navigation_fens || [data.fen],
                data.navigation_sans || [],
                0
            );

            updateHistory(data.history, data.history_items);
        }

        updateStatus(data.message);
    } catch {
        updateStatus('Fehler beim Zurücksetzen.');
    }
}

function flipBoard() {
    window.Board.flip(boardInteractionOptions());
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
            body: JSON.stringify({ fen }),
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
            number1,
            number2,
            select1,
            select2,
        }),
    })
        .then(response => response.json())
        .then(data => {
            console.log('Antwort von /generate_task:', data);

            if (data.ok) {
                userHasAnswered = false;
                solutionShown = false;

                window.Board.setOrientationFromFen(data.fen);

                setNavigationLine(
                    data.navigation_fens || [data.fen],
                    data.navigation_sans || [],
                    0
                );

                updateHistory(data.history, data.history_items);
                if (data.parameter) {
                  const adminLinkEl = document.getElementById("adminParameterLink");

                  if (adminLinkEl) {
                    const url = new URL(window.location.href);
                    url.searchParams.set("parameter", data.parameter);
                    adminLinkEl.textContent = url.toString();
                  }
                }
            }

            updateStatus(data.message);
        })
        .catch(error => {
            console.error(error);
            updateStatus('Fehler beim Generieren der Aufgabe');
        });
}

async function showSolution() {
    try {
        const response = await fetch('/visualisierung/solution');
        const data = await response.json();

        if (data.ok) {
            solutionShown = true;

            updateHistory(data.history, data.history_items);

            setNavigationLine(
                data.navigation_fens || navigationFens,
                data.navigation_sans || navigationSans,
                navigationIndex
            );
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
            let message = 'Fehler beim Download';

            try {
                const data = await response.json();
                message = data.message || message;
            } catch {
                // Fallback bleibt bestehen.
            }

            alert(message);
            return;
        }

        const blob = await response.blob();

        let filename = 'aufgabe.pgn';
        const disposition = response.headers.get('Content-Disposition');

        if (disposition && disposition.includes('filename')) {
            const match = disposition.match(/filename="?([^"]+)"?/);

            if (match) {
                filename = match[1];
            }
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');

        a.href = url;
        a.download = filename;

        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
    } catch {
        alert('Netzwerkfehler beim Download');
    }
}

async function checkSolutionMove(move) {
    try {
        const response = await fetch('/visualisierung/check_solution_move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ move }),
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

function bindEvents() {
    document.getElementById('moveBtn')?.addEventListener('click', () => sendMove());
    document.getElementById('resetBtn')?.addEventListener('click', resetBoard);
    document.getElementById('flipBtn')?.addEventListener('click', flipBoard);
    document.getElementById('fenBtn')?.addEventListener('click', setFen);
    document.getElementById('generateTaskBtn')?.addEventListener('click', generateTask);
    document.getElementById('showSolutionBtn')?.addEventListener('click', showSolution);
    document.getElementById('prevMoveBtn')?.addEventListener('click', goToPreviousMove);
    document.getElementById('nextMoveBtn')?.addEventListener('click', goToNextMove);
    document.getElementById('downloadPgnBtn')?.addEventListener('click', downloadPgn);

    document.getElementById('moveInput')?.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
            sendMove();
        }
    });

    document.getElementById('fenInput')?.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
            setFen();
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    bindEvents();

    window.Board.setFenAndOrientation(
        window.INITIAL_FEN || 'start',
        boardInteractionOptions()
    );

    setNavigationLine([window.Board.getFen()], [], 0);
});

document.addEventListener('DOMContentLoaded', () => {
  bindEvents();

  if (window.INITIAL_TASK) {
    window.Board.setFenAndOrientation(
      window.INITIAL_TASK.fen,
      boardInteractionOptions()
    );

    setNavigationLine(
      window.INITIAL_TASK.navigation_fens || [window.INITIAL_TASK.fen],
      window.INITIAL_TASK.navigation_sans || [],
      0
    );

    updateHistory(
      window.INITIAL_TASK.history,
      window.INITIAL_TASK.history_items
    );

    return;
  }

  window.Board.setFenAndOrientation(
    window.INITIAL_FEN || 'start',
    boardInteractionOptions()
  );

  setNavigationLine([window.Board.getFen()], [], 0);
});

// Legacy-Zugriffe für eventuell noch vorhandene inline onclick-Handler.
window.generateTask = generateTask;
window.showSolution = showSolution;
window.downloadPgn = downloadPgn;
window.goToPreviousMove = goToPreviousMove;
window.goToNextMove = goToNextMove;
window.flipBoard = flipBoard;
window.resetBoard = resetBoard;
window.sendMove = sendMove;
window.setFen = setFen;

