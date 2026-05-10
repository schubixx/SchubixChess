const PIECE_IMAGE_MAP = {
    P: 'wP', N: 'wN', B: 'wB', R: 'wR', Q: 'wQ', K: 'wK',
    p: 'bP', n: 'bN', b: 'bB', r: 'bR', q: 'bQ', k: 'bK'
};

let boardFen = window.INITIAL_FEN || 'start';
let boardOrientation = 'white';
let draggedFrom = null;

function getPieceSet() {
    return window.PIECE_SET || 'merida';
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
                for (let i = 0; i < Number(ch); i += 1) {
                    cells.push(null);
                }
            } else {
                cells.push(ch);
            }
        }

        while (cells.length < 8) {
            cells.push(null);
        }

        return cells.slice(0, 8);
    });
}

function setOrientationFromFen(fen) {
    const parts = (fen || '').split(' ');
    const sideToMove = parts.length > 1 ? parts[1] : 'w';
    boardOrientation = sideToMove === 'b' ? 'black' : 'white';
}

function coordsToSquare(row, col) {
    const file = 'abcdefgh'[col];
    const rank = String(8 - row);
    return `${file}${rank}`;
}

function displayOrder() {
    const rows = [...Array(8).keys()];
    const cols = [...Array(8).keys()];

    if (boardOrientation === 'black') {
        rows.reverse();
        cols.reverse();
    }

    return { rows, cols };
}

function renderOuterCoordinates() {
    const topFilesEl = document.getElementById('boardTopFiles');
    const bottomFilesEl = document.getElementById('boardBottomFiles');
    const leftRanksEl = document.getElementById('boardRanksLeft');
    const rightRanksEl = document.getElementById('boardRanksRight');

    if (!topFilesEl || !bottomFilesEl || !leftRanksEl || !rightRanksEl) {
        return;
    }

    topFilesEl.innerHTML = '';
    bottomFilesEl.innerHTML = '';
    leftRanksEl.innerHTML = '';
    rightRanksEl.innerHTML = '';

    const files = boardOrientation === 'white'
        ? ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        : ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'];

    const ranks = boardOrientation === 'white'
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
    document
        .querySelectorAll('.square.highlight')
        .forEach(el => el.classList.remove('highlight'));
}

function renderBoard(options = {}) {
    const boardEl = document.getElementById('board');

    if (!boardEl) {
        return;
    }

    const onSquareClick = options.onSquareClick || null;
    const onMove = options.onMove || null;
    const enableDrag = Boolean(options.enableDrag && onMove);

    boardEl.innerHTML = '';

    const state = parseFenBoard(boardFen);
    const { rows, cols } = displayOrder();

    rows.forEach(row => {
        cols.forEach(col => {
            const squareName = coordsToSquare(row, col);
            const squareEl = document.createElement('div');

            squareEl.className = `square ${(row + col) % 2 === 0 ? 'light' : 'dark'}`;
            squareEl.dataset.square = squareName;

            if (onSquareClick) {
                squareEl.addEventListener('click', () => {
                    onSquareClick(squareEl, squareName);
                });
            }

            if (enableDrag) {
                squareEl.addEventListener('dragover', event => {
                    event.preventDefault();
                });

                squareEl.addEventListener('drop', event => {
                    event.preventDefault();

                    const from = event.dataTransfer.getData('text/plain') || draggedFrom;
                    const to = squareName;

                    clearHighlights();

                    if (from && to) {
                        onMove(`${from}${to}`);
                    }

                    draggedFrom = null;
                });

                squareEl.addEventListener('dragenter', () => {
                    squareEl.classList.add('highlight');
                });

                squareEl.addEventListener('dragleave', () => {
                    squareEl.classList.remove('highlight');
                });
            }

            const piece = state[row][col];

            if (piece) {
                const pieceEl = document.createElement('img');
                pieceEl.className = `piece ${piece === piece.toUpperCase() ? 'white' : 'black'}`;
                pieceEl.src = `/static/img/chesspieces/${getPieceSet()}/${PIECE_IMAGE_MAP[piece]}.svg`;
                pieceEl.alt = piece;
                pieceEl.draggable = enableDrag;
                pieceEl.dataset.square = squareName;

                if (enableDrag) {
                    pieceEl.addEventListener('dragstart', event => {
                        draggedFrom = squareName;
                        event.dataTransfer.setData('text/plain', squareName);
                        pieceEl.classList.add('dragging');
                    });

                    pieceEl.addEventListener('dragend', () => {
                        pieceEl.classList.remove('dragging');
                        clearHighlights();
                    });
                }

                squareEl.appendChild(pieceEl);
            }

            boardEl.appendChild(squareEl);
        });
    });

    renderOuterCoordinates();
}

function setBoardFen(fen, options = {}) {
    boardFen = fen;
    renderBoard(options);
}

function setBoardFenAndOrientation(fen, options = {}) {
    boardFen = fen;
    setOrientationFromFen(fen);
    renderBoard(options);
}

function flipBoard(options = {}) {
    boardOrientation = boardOrientation === 'white' ? 'black' : 'white';
    renderBoard(options);
}

document.addEventListener('DOMContentLoaded', () => {
    setOrientationFromFen(boardFen);
    renderBoard();
});

window.Board = {
    render: renderBoard,
    setFen: setBoardFen,
    setFenAndOrientation: setBoardFenAndOrientation,
    setOrientationFromFen,
    flip: flipBoard,
    getFen: () => boardFen,
    getOrientation: () => boardOrientation,
    clearHighlights,
};
