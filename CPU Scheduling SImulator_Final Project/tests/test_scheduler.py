import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from scheduler import Process, compare_all, fcfs, priority_scheduling, round_robin, sjf, srtf


def sample_processes():
    return [
        Process("P1", 0, 7, 2),
        Process("P2", 2, 4, 1),
        Process("P3", 4, 1, 3),
        Process("P4", 5, 4, 2),
        Process("P5", 6, 3, 1),
    ]


def assert_valid(result):
    assert len(result.metrics) == 5
    assert result.avg_waiting >= 0
    assert result.avg_turnaround > 0
    assert all(segment.end > segment.start for segment in result.segments)
    assert {metric.pid for metric in result.metrics} == {"P1", "P2", "P3", "P4", "P5"}


def test_fcfs():
    assert_valid(fcfs(sample_processes()))


def test_sjf():
    assert_valid(sjf(sample_processes()))


def test_srtf():
    assert_valid(srtf(sample_processes()))


def test_priority():
    assert_valid(priority_scheduling(sample_processes()))


def test_round_robin():
    assert_valid(round_robin(sample_processes(), quantum=2))


def test_compare_all():
    results = compare_all(sample_processes(), quantum=2)
    assert len(results) == 5
    for result in results:
        assert_valid(result)
