# 8-Puzzle Game in Python with Flask - Debugged Version
# Complete application in a single file for easy deployment

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import random
import time
import heapq
from collections import deque
from typing import List, Tuple, Dict, Optional
import uuid
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app)

# Store game sessions (in production, use Redis or a database)
game_sessions = {}

# HTML Template with minimal design
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>8-Puzzle Game</title>
    <style>
        body {
            font-family: monospace;
            margin: 20px;
        }

        .puzzle {
            display: inline-grid;
            grid-template-columns: repeat(3, 60px);
            grid-template-rows: repeat(3, 60px);
            gap: 2px;
            border: 2px solid black;
            margin: 10px;
            vertical-align: top;
        }

        .puzzle-piece {
            width: 60px;
            height: 60px;
            border: 1px solid black;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
            background: white;
        }

        .puzzle-piece.empty {
            background-color: #ddd;
            cursor: default;
        }

        button {
            margin: 5px;
            padding: 5px 10px;
            font-family: monospace;
        }

        select {
            margin: 5px;
            padding: 5px;
            font-family: monospace;
        }

        .section {
            margin: 20px 0;
        }

        .puzzle-wrapper {
            display: inline-block;
            margin: 10px;
            vertical-align: top;
        }

        .solution-step {
            font-family: monospace;
            margin: 2px 0;
        }

        #loading {
            color: red;
        }

        #solutionSteps {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 5px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h1>8-Puzzle Game</h1>

    <div class="section">
        <label>Algorithm:</label>
        <select id="algorithmSelect">
            <option value="astar_manhattan">A* (Manhattan Distance)</option>
            <option value="astar_misplaced">A* (Misplaced Tiles)</option>
            <option value="bfs">Breadth-First Search (BFS)</option>
            <option value="dfs">Depth-First Search (DFS - Limited)</option>
            <option value="greedy">Greedy Best-First Search</option>
        </select>
    </div>

    <div class="section">
        <button onclick="newGame()">New Game</button>
        <button onclick="shufflePuzzle()">Shuffle</button>
        <button onclick="solvePuzzle()">Solve</button>
        <button onclick="resetPuzzle()">Reset</button>
        <button onclick="animateSolution()">Animate Solution</button>
    </div>

    <div class="section">
        <div class="puzzle-wrapper">
            <strong>Current State</strong>
            <div class="puzzle" id="currentPuzzle"></div>
            <div>Moves: <span id="moveCount">0</span></div>
            <div>Status: <span id="gameStatus">Ready</span></div>
            <div>Session: <span id="sessionId">-</span></div>
        </div>

        <div class="puzzle-wrapper">
            <strong>Goal State</strong>
            <div class="puzzle" id="targetPuzzle"></div>
        </div>
    </div>

    <div id="loading" style="display: none;">Solving puzzle...</div>

    <div id="successMessage" style="display: none;"></div>

    <div id="solutionContainer" style="display: none;">
        <h3>Solution</h3>
        <div id="solutionInfo"></div>
        <div id="solutionSteps"></div>
    </div>

    <script>
        let sessionId = null;
        let currentSolution = null;
        let isAnimating = false;

        // Initialize game on page load
        window.onload = function() {
            newGame();
        };

        // Create new game
        async function newGame() {
            try {
                const response = await fetch('/api/new_game', { method: 'POST' });
                const data = await response.json();
                sessionId = data.session_id;
                document.getElementById('sessionId').textContent = sessionId.substring(0, 8);
                updatePuzzleDisplay(data.state, data.moves);
            } catch (error) {
                console.error('Error creating new game:', error);
            }
        }

        // Shuffle puzzle
        async function shufflePuzzle() {
            if (isAnimating) return;
            try {
                const response = await fetch('/api/shuffle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                const data = await response.json();
                updatePuzzleDisplay(data.state, data.moves);
                hideSolution();
                hideSuccess();
            } catch (error) {
                console.error('Error shuffling puzzle:', error);
            }
        }

        // Reset puzzle
        async function resetPuzzle() {
            if (isAnimating) return;
            try {
                const response = await fetch('/api/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                const data = await response.json();
                updatePuzzleDisplay(data.state, data.moves);
                hideSolution();
                hideSuccess();
            } catch (error) {
                console.error('Error resetting puzzle:', error);
            }
        }

        // Make move
        async function makeMove(index) {
            if (isAnimating) return;
            try {
                const response = await fetch('/api/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        session_id: sessionId,
                        position: index 
                    })
                });
                const data = await response.json();

                if (data.valid_move) {
                    updatePuzzleDisplay(data.state, data.moves);

                    if (data.solved) {
                        showSuccess(data.moves);
                    }
                }
            } catch (error) {
                console.error('Error making move:', error);
            }
        }

        // Solve puzzle
        async function solvePuzzle() {
            if (isAnimating) return;

            const algorithm = document.getElementById('algorithmSelect').value;
            document.getElementById('loading').style.display = 'block';
            hideSolution();
            hideSuccess();

            try {
                const response = await fetch('/api/solve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        session_id: sessionId,
                        algorithm: algorithm 
                    })
                });
                const data = await response.json();

                document.getElementById('loading').style.display = 'none';

                if (data.success) {
                    currentSolution = data.solution;
                    displaySolution(data);
                } else {
                    alert(data.message || 'Could not find solution');
                }
            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                console.error('Error solving puzzle:', error);
                alert('Error solving puzzle');
            }
        }

        // Update puzzle display
        function updatePuzzleDisplay(state, moves) {
            // Update current puzzle
            const currentPuzzle = document.getElementById('currentPuzzle');
            currentPuzzle.innerHTML = '';

            for (let i = 0; i < 9; i++) {
                const piece = document.createElement('div');
                piece.className = 'puzzle-piece';

                if (state[i] === 0) {
                    piece.classList.add('empty');
                } else {
                    piece.textContent = state[i];
                    piece.onclick = () => makeMove(i);
                }

                currentPuzzle.appendChild(piece);
            }

            // Update target puzzle (only once)
            const targetPuzzle = document.getElementById('targetPuzzle');
            if (targetPuzzle.children.length === 0) {
                const goalState = [1, 2, 3, 4, 5, 6, 7, 8, 0];
                for (let i = 0; i < 9; i++) {
                    const piece = document.createElement('div');
                    piece.className = 'puzzle-piece';
                    if (goalState[i] === 0) {
                        piece.classList.add('empty');
                    } else {
                        piece.textContent = goalState[i];
                    }
                    targetPuzzle.appendChild(piece);
                }
            }

            // Update stats
            document.getElementById('moveCount').textContent = moves;

            // Check if solved
            const goalState = [1, 2, 3, 4, 5, 6, 7, 8, 0];
            const isSolved = state.every((val, idx) => val === goalState[idx]);
            document.getElementById('gameStatus').textContent = isSolved ? 'Solved!' : 'Playing';
        }

        // Display solution
        function displaySolution(data) {
            const container = document.getElementById('solutionContainer');
            const info = document.getElementById('solutionInfo');
            const steps = document.getElementById('solutionSteps');

            info.innerHTML = `Algorithm: ${data.algorithm} | Steps: ${data.steps} | Time: ${data.time.toFixed(3)}s | Nodes: ${data.nodes_explored || 'N/A'}`;

            steps.innerHTML = '';
            data.solution.forEach((state, index) => {
                const stepDiv = document.createElement('div');
                stepDiv.className = 'solution-step';
                stepDiv.textContent = `Step ${index}: [${state.join(', ')}]`;
                steps.appendChild(stepDiv);
            });

            container.style.display = 'block';
        }

        // Animate solution
        async function animateSolution() {
            if (!currentSolution || isAnimating) return;

            isAnimating = true;
            for (let i = 0; i < currentSolution.length; i++) {
                updatePuzzleDisplay(currentSolution[i], i);
                await sleep(500);
            }
            isAnimating = false;

            // Check if solved
            const finalState = currentSolution[currentSolution.length - 1];
            const goalState = [1, 2, 3, 4, 5, 6, 7, 8, 0];
            if (finalState.every((val, idx) => val === goalState[idx])) {
                showSuccess(currentSolution.length - 1);
            }
        }

        // Utility functions
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        function hideSolution() {
            document.getElementById('solutionContainer').style.display = 'none';
            currentSolution = null;
        }

        function showSuccess(moves) {
            const msg = document.getElementById('successMessage');
            msg.textContent = `Puzzle solved in ${moves} moves!`;
            msg.style.display = 'block';
        }

        function hideSuccess() {
            document.getElementById('successMessage').style.display = 'none';
        }
    </script>
</body>
</html>
'''


class PuzzleState:
    """Represents a state of the 8-puzzle"""

    def __init__(self, state: List[int], parent=None, move=None, depth=0):
        self.state = state
        self.parent = parent
        self.move = move
        self.depth = depth
        self.hash = tuple(state)

    def __eq__(self, other):
        return self.hash == other.hash

    def __hash__(self):
        return hash(self.hash)

    def __lt__(self, other):
        return False  # For heap comparison

    def get_blank_position(self) -> int:
        return self.state.index(0)

    def get_neighbors(self) -> List['PuzzleState']:
        """Get all valid neighbor states"""
        neighbors = []
        blank_pos = self.get_blank_position()
        row, col = blank_pos // 3, blank_pos % 3

        # Possible moves: up, down, left, right
        moves = [
            (-1, 0, blank_pos - 3),  # up
            (1, 0, blank_pos + 3),  # down
            (0, -1, blank_pos - 1),  # left
            (0, 1, blank_pos + 1)  # right
        ]

        for dr, dc, new_pos in moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 3 and 0 <= new_col < 3:
                # Additional check to prevent wrapping
                if abs((new_pos % 3) - (blank_pos % 3)) <= 1 or abs(new_pos - blank_pos) == 3:
                    new_state = self.state.copy()
                    new_state[blank_pos], new_state[new_pos] = new_state[new_pos], new_state[blank_pos]
                    neighbors.append(PuzzleState(new_state, self, new_pos, self.depth + 1))

        return neighbors

    def is_goal(self) -> bool:
        return self.state == [1, 2, 3, 4, 5, 6, 7, 8, 0]

    def manhattan_distance(self) -> int:
        """Calculate Manhattan distance heuristic"""
        distance = 0
        for i in range(9):
            if self.state[i] != 0:
                current_row, current_col = i // 3, i % 3
                goal_pos = self.state[i] - 1
                goal_row, goal_col = goal_pos // 3, goal_pos % 3
                distance += abs(current_row - goal_row) + abs(current_col - goal_col)
        return distance

    def misplaced_tiles(self) -> int:
        """Count misplaced tiles heuristic"""
        goal = [1, 2, 3, 4, 5, 6, 7, 8, 0]
        return sum(1 for i in range(9) if self.state[i] != 0 and self.state[i] != goal[i])


class PuzzleSolver:
    """Solver for 8-puzzle using various algorithms"""

    @staticmethod
    def reconstruct_path(final_state: PuzzleState) -> List[List[int]]:
        """Reconstruct solution path from final state"""
        path = []
        current = final_state
        while current:
            path.append(current.state)
            current = current.parent
        return list(reversed(path))

    @staticmethod
    def astar_search(initial_state: List[int], heuristic='manhattan') -> Tuple[List[List[int]], int]:
        """A* search algorithm"""
        start = PuzzleState(initial_state)
        if start.is_goal():
            return [initial_state], 0

        # Priority queue: (f_score, counter, state)
        counter = 0
        open_set = []
        heapq.heappush(open_set, (0, counter, start))

        # Track best g_score for each state
        g_score = {start.hash: 0}
        closed_set = set()
        nodes_explored = 0
        max_nodes = 100000  # Prevent infinite loops

        while open_set and nodes_explored < max_nodes:
            _, _, current = heapq.heappop(open_set)

            if current.hash in closed_set:
                continue

            nodes_explored += 1

            if current.is_goal():
                return PuzzleSolver.reconstruct_path(current), nodes_explored

            closed_set.add(current.hash)

            for neighbor in current.get_neighbors():
                if neighbor.hash in closed_set:
                    continue

                tentative_g = g_score[current.hash] + 1

                if neighbor.hash not in g_score or tentative_g < g_score[neighbor.hash]:
                    g_score[neighbor.hash] = tentative_g

                    if heuristic == 'manhattan':
                        h = neighbor.manhattan_distance()
                    else:
                        h = neighbor.misplaced_tiles()

                    f_score = tentative_g + h
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor))

        return None, nodes_explored

    @staticmethod
    def bfs_search(initial_state: List[int]) -> Tuple[List[List[int]], int]:
        """Breadth-first search"""
        start = PuzzleState(initial_state)
        if start.is_goal():
            return [initial_state], 0

        queue = deque([start])
        visited = {start.hash}
        nodes_explored = 0
        max_nodes = 100000

        while queue and nodes_explored < max_nodes:
            current = queue.popleft()
            nodes_explored += 1

            for neighbor in current.get_neighbors():
                if neighbor.hash not in visited:
                    if neighbor.is_goal():
                        return PuzzleSolver.reconstruct_path(neighbor), nodes_explored

                    visited.add(neighbor.hash)
                    queue.append(neighbor)

        return None, nodes_explored

    @staticmethod
    def dfs_search(initial_state: List[int], max_depth: int = 20) -> Tuple[List[List[int]], int]:
        """Depth-first search with depth limit"""
        start = PuzzleState(initial_state)
        if start.is_goal():
            return [initial_state], 0

        stack = [start]
        visited = set()
        nodes_explored = 0

        while stack and nodes_explored < 10000:  # Limit nodes for DFS
            current = stack.pop()

            if current.hash in visited or current.depth > max_depth:
                continue

            visited.add(current.hash)
            nodes_explored += 1

            if current.is_goal():
                return PuzzleSolver.reconstruct_path(current), nodes_explored

            # Add neighbors in reverse order for consistent DFS behavior
            for neighbor in reversed(current.get_neighbors()):
                if neighbor.hash not in visited:
                    stack.append(neighbor)

        return None, nodes_explored

    @staticmethod
    def greedy_search(initial_state: List[int]) -> Tuple[List[List[int]], int]:
        """Greedy best-first search"""
        start = PuzzleState(initial_state)
        if start.is_goal():
            return [initial_state], 0

        counter = 0
        open_set = []
        heapq.heappush(open_set, (start.manhattan_distance(), counter, start))
        visited = set()
        nodes_explored = 0
        max_nodes = 50000

        while open_set and nodes_explored < max_nodes:
            _, _, current = heapq.heappop(open_set)

            if current.hash in visited:
                continue

            visited.add(current.hash)
            nodes_explored += 1

            if current.is_goal():
                return PuzzleSolver.reconstruct_path(current), nodes_explored

            for neighbor in current.get_neighbors():
                if neighbor.hash not in visited:
                    counter += 1
                    heapq.heappush(open_set, (neighbor.manhattan_distance(), counter, neighbor))

        return None, nodes_explored


class GameSession:
    """Represents a game session"""

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.state = [1, 2, 3, 4, 5, 6, 7, 8, 0]
        self.moves = 0
        self.start_time = time.time()

    def shuffle(self):
        """Shuffle the puzzle to a solvable state"""
        # Start from goal state and make random valid moves
        self.state = [1, 2, 3, 4, 5, 6, 7, 8, 0]
        puzzle_state = PuzzleState(self.state)

        # Make 50-100 random moves from solved state
        num_shuffles = random.randint(50, 100)
        for _ in range(num_shuffles):
            neighbors = puzzle_state.get_neighbors()
            if neighbors:
                puzzle_state = random.choice(neighbors)
                self.state = puzzle_state.state.copy()

        self.moves = 0

    def reset(self):
        """Reset to goal state"""
        self.state = [1, 2, 3, 4, 5, 6, 7, 8, 0]
        self.moves = 0

    def make_move(self, position: int) -> bool:
        """Attempt to move a piece at given position"""
        if position < 0 or position >= 9:
            return False

        blank_pos = self.state.index(0)

        # Check if move is valid (adjacent to blank)
        row1, col1 = position // 3, position % 3
        row2, col2 = blank_pos // 3, blank_pos % 3

        # Check if adjacent (not diagonal)
        if abs(row1 - row2) + abs(col1 - col2) == 1:
            # Valid move - swap pieces
            self.state[blank_pos], self.state[position] = self.state[position], self.state[blank_pos]
            self.moves += 1
            return True
        return False

    def is_solved(self) -> bool:
        """Check if puzzle is solved"""
        return self.state == [1, 2, 3, 4, 5, 6, 7, 8, 0]


# Routes
@app.route('/')
def index():
    """Serve the main game page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Create a new game session"""
    session = GameSession()
    session.shuffle()
    game_sessions[session.session_id] = session

    return jsonify({
        'session_id': session.session_id,
        'state': session.state,
        'moves': session.moves
    })


@app.route('/api/shuffle', methods=['POST'])
def shuffle():
    """Shuffle the current puzzle"""
    data = request.json
    session_id = data.get('session_id')

    if session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = game_sessions[session_id]
    session.shuffle()

    return jsonify({
        'state': session.state,
        'moves': session.moves
    })


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset puzzle to solved state"""
    data = request.json
    session_id = data.get('session_id')

    if session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = game_sessions[session_id]
    session.reset()

    return jsonify({
        'state': session.state,
        'moves': session.moves
    })


@app.route('/api/move', methods=['POST'])
def move():
    """Make a move in the puzzle"""
    data = request.json
    session_id = data.get('session_id')
    position = data.get('position')

    if session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400

    if position is None:
        return jsonify({'error': 'Position required'}), 400

    session = game_sessions[session_id]
    valid_move = session.make_move(position)

    return jsonify({
        'valid_move': valid_move,
        'state': session.state,
        'moves': session.moves,
        'solved': session.is_solved()
    })


@app.route('/api/solve', methods=['POST'])
def solve():
    """Solve the current puzzle"""
    data = request.json
    session_id = data.get('session_id')
    algorithm = data.get('algorithm', 'astar_manhattan')

    if session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400

    session = game_sessions[session_id]
    start_time = time.time()

    try:
        # Choose algorithm
        if algorithm == 'astar_manhattan':
            solution, nodes = PuzzleSolver.astar_search(session.state, 'manhattan')
            algorithm_name = 'A* (Manhattan Distance)'
        elif algorithm == 'astar_misplaced':
            solution, nodes = PuzzleSolver.astar_search(session.state, 'misplaced')
            algorithm_name = 'A* (Misplaced Tiles)'
        elif algorithm == 'bfs':
            solution, nodes = PuzzleSolver.bfs_search(session.state)
            algorithm_name = 'Breadth-First Search'
        elif algorithm == 'dfs':
            solution, nodes = PuzzleSolver.dfs_search(session.state)
            algorithm_name = 'Depth-First Search (Limited)'
        elif algorithm == 'greedy':
            solution, nodes = PuzzleSolver.greedy_search(session.state)
            algorithm_name = 'Greedy Best-First Search'
        else:
            solution, nodes = PuzzleSolver.astar_search(session.state, 'manhattan')
            algorithm_name = 'A* (Manhattan Distance)'

        solve_time = time.time() - start_time

        if solution:
            return jsonify({
                'success': True,
                'solution': solution,
                'steps': len(solution) - 1,
                'time': solve_time,
                'algorithm': algorithm_name,
                'nodes_explored': nodes
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No solution found within search limits'
            })

    except Exception as e:
        print(f"Error in solve endpoint: {str(e)}")  # Debug logging
        return jsonify({
            'success': False,
            'message': f'Error solving puzzle: {str(e)}'
        }), 500


@app.route('/api/check_solvable', methods=['POST'])
def check_solvable():
    """Check if a puzzle state is solvable"""
    data = request.json
    state = data.get('state', [])

    def count_inversions(state):
        """Count inversions in the puzzle state"""
        inv_count = 0
        for i in range(9):
            for j in range(i + 1, 9):
                if state[i] and state[j] and state[i] > state[j]:
                    inv_count += 1
        return inv_count

    # A puzzle is solvable if the number of inversions is even
    inversions = count_inversions(state)
    is_solvable = inversions % 2 == 0

    return jsonify({
        'solvable': is_solvable,
        'inversions': inversions
    })


# Cleanup old sessions periodically (optional)
def cleanup_old_sessions():
    """Remove sessions older than 1 hour"""
    current_time = time.time()
    to_remove = []
    for sid, session in game_sessions.items():
        if current_time - session.start_time > 3600:  # 1 hour
            to_remove.append(sid)
    for sid in to_remove:
        del game_sessions[sid]


if __name__ == '__main__':
    # Run the Flask app
    print("=" * 50)
    print("8-PUZZLE GAME SERVER")
    print("=" * 50)
    print("Starting server...")
    print("Open http://localhost:5000 in your browser to play!")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    app.run(debug=False, port=5050, host='0.0.0.0')