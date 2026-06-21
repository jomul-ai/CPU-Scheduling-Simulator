# CPU Scheduling Simulator

A Python-based CPU Scheduling Simulator with a modern graphical user interface developed using Tkinter. This application allows users to simulate and compare different CPU scheduling algorithms, visualize process execution through a Gantt Chart, and analyze scheduling performance metrics.

---

## Features

- Interactive graphical user interface (GUI)
- Support for multiple CPU scheduling algorithms:
  - First Come First Serve (FCFS)
  - Shortest Job First (SJF)
  - Shortest Remaining Time First (SRTF)
  - Priority Scheduling
  - Round Robin Scheduling
- Gantt Chart visualization
- Animated scheduling execution
- Performance metrics calculation:
  - Completion Time
  - Waiting Time
  - Turnaround Time
- Random workload generation
- Sample workload loading
- CSV export functionality
- Input validation and error handling
- Light/Dark theme support

---

## Technologies Used

- Python 3
- Tkinter
- ttk
- Dataclasses
- CSV Module
- Pytest (Unit Testing)

---

## Project Structure

```
CPU-Scheduling-Simulator/
│
├── src/
│   ├── main.py
│   └── scheduler.py
│
├── tests/
│   └── test_scheduler.py
│
└── README.md
```

---

## Scheduling Algorithms

### FCFS (First Come First Serve)
Processes are executed according to their arrival order.

### SJF (Shortest Job First)
Processes with the shortest burst time are executed first.

### SRTF (Shortest Remaining Time First)
A preemptive version of SJF that always executes the process with the shortest remaining execution time.

### Priority Scheduling
Processes are executed based on their priority level.

### Round Robin
Processes are executed cyclically using a fixed time quantum.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/jomul-ai/CPU-Scheduling-Simulator.git
```

Navigate to the project folder:

```bash
cd CPU-Scheduling-Simulator
```

Run the application:

```bash
python src/main.py
```

---

## Running Unit Tests

To execute all tests:

```bash
pytest
```

or

```bash
python -m pytest
```

---

## Example Process Data

| Process | Arrival Time | Burst Time | Priority |
|----------|-------------|------------|------------|
| P1 | 0 | 8 | 3 |
| P2 | 1 | 4 | 1 |
| P3 | 2 | 2 | 2 |
| P4 | 3 | 6 | 4 |
| P5 | 4 | 3 | 2 |

Round Robin Quantum = 2

---

## Performance Comparison

| Algorithm | Average Waiting Time | Average Turnaround Time |
|------------|--------------------|-------------------------|
| FCFS | 8.8 | 13.4 |
| SJF | 7.6 | 12.2 |
| SRTF | 5.4 | 10.0 |
| Priority Scheduling | 8.2 | 12.8 |
| Round Robin | 10.0 | 14.6 |

Based on the experimental results, SRTF achieved the best performance by producing the lowest average waiting time and average turnaround time.

---

## Learning Outcomes

Through this project, we gained practical experience in:

- CPU Scheduling Algorithms
- Operating System Concepts
- Python Programming
- GUI Development with Tkinter
- Software Testing and Debugging
- Data Visualization
- Performance Analysis

---

## Authors

Final Project – CPU Scheduling Simulator

Team Members:

- Jonathan Mulyono
- Bagaskara Leo

---

