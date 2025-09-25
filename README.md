# 8-Puzzle Game Implementation

**Author:** Daniel Reyes  
**Date:** September 25, 2025  
**Course:** CAI4002

**PANTHERID:** 6519474

---

## Overview
A web-based 8-puzzle game that converts uploaded images into playable sliding puzzles. Implements A* algorithm with multiple heuristics and provides automated solving with step-by-step visualization.

## Installation & Usage

### Requirements
- Python 3.7+
- Flask, Flask-CORS

### Setup
```bash
pip install flask flask-cors
python puzzle_game.py
# Open browser to http://localhost:5000
```

### How to Play
1. Upload an image (optional) or use numbered tiles
2. Click "Shuffle" to scramble
3. Click tiles adjacent to empty space to move
4. Select algorithm and click "Solve" for solution
5. Click "Animate Solution" to watch automated solving

## Core Algorithm: A* Implementation

### Manhattan Distance Heuristic (Primary)
```
h(n) = Σ |current_row - goal_row| + |current_col - goal_col|
```
**Rationale:** This heuristic is:
- **Admissible:** Never overestimates actual cost
- **Consistent:** Satisfies triangle inequality  
- **Efficient:** Provides optimal solutions with fewer node expansions than other heuristics

The Manhattan distance calculates the sum of horizontal and vertical distances each tile must travel to reach its goal position, making it ideal for grid-based puzzles where diagonal moves are not allowed.

### Misplaced Tiles Heuristic (Alternative)
```
h(n) = count of tiles not in goal position
```
**Rationale:** Simpler but less informed than Manhattan. Still admissible and guarantees optimal solutions.

## Features Implemented

### Required Features ✓
- **A* Algorithm** with Manhattan Distance heuristic (60 pts)
- **User-friendly web interface** (40 pts)
- **Image upload** and conversion to puzzle
- **Shuffle** functionality  
- **Solution display** with optimal path

### Extra Features (20 pts)
1. **Multiple Algorithms:** A*, BFS, DFS, Greedy for comparison
2. **Solution Animation:** Step-by-step playback
3. **Performance Metrics:** Nodes explored, solving time
4. **Number Overlays:** Tile numbers on image pieces
5. **Session Management:** Multiple concurrent users

## Algorithm Comparison

| Algorithm | Optimality | Completeness | Nodes Explored (avg) |
|-----------|------------|--------------|---------------------|
| A* (Manhattan) | Yes | Yes | ~500-2000 |
| A* (Misplaced) | Yes | Yes | ~1000-5000 |
| BFS | Yes | Yes | ~5000-20000 |
| DFS (Limited) | No | No | ~100-1000 |
| Greedy | No | No | ~200-2000 |

## File Structure
```
8-puzzle-game/
├── puzzle_game.py      # Main application
├── README.pdf          # This document
└── requirements.txt    # Dependencies
```

## Technical Implementation

- **Backend:** Flask web framework (Python)
- **Frontend:** HTML5, CSS, JavaScript
- **State Representation:** List of 9 integers (0 represents empty)
- **Search Optimization:** Priority queue with heap, node exploration limits
- **Image Processing:** CSS background positioning for tile display

## Testing Results
- ✓ All algorithms produce correct solutions
- ✓ Image formats: JPG, PNG (up to 10MB)
- ✓ Average solve time: <1 second
- ✓ Handles edge cases: solved states, maximum shuffling
