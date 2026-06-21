from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int


@dataclass(frozen=True)
class Segment:
    pid: str
    start: int
    end: int


@dataclass(frozen=True)
class Metric:
    pid: str
    arrival: int
    burst: int
    priority: int
    completion: int
    turnaround: int
    waiting: int


@dataclass(frozen=True)
class ScheduleResult:
    algorithm: str
    segments: List[Segment]
    metrics: List[Metric]
    avg_waiting: float
    avg_turnaround: float
    execution_order: List[str]


def _validate_processes(processes: List[Process]) -> None:
    if not processes:
        raise ValueError("Please add at least one process.")
    seen = set()
    for process in processes:
        if not process.pid.strip():
            raise ValueError("Process ID cannot be empty.")
        if process.pid in seen:
            raise ValueError(f"Duplicate Process ID found: {process.pid}")
        seen.add(process.pid)
        if process.arrival < 0:
            raise ValueError(f"Arrival time for {process.pid} must be zero or positive.")
        if process.burst <= 0:
            raise ValueError(f"Burst time for {process.pid} must be greater than zero.")
        if process.priority < 0:
            raise ValueError(f"Priority value for {process.pid} must be zero or positive.")


def _merge_or_append(segments: List[Segment], pid: str, start: int, end: int) -> None:
    if end <= start:
        return
    if segments and segments[-1].pid == pid and segments[-1].end == start:
        previous = segments[-1]
        segments[-1] = Segment(pid=pid, start=previous.start, end=end)
    else:
        segments.append(Segment(pid=pid, start=start, end=end))


def _build_result(
    algorithm: str,
    processes: List[Process],
    segments: List[Segment],
    completion_times: Dict[str, int],
) -> ScheduleResult:
    metrics: List[Metric] = []

    for process in sorted(processes, key=lambda item: item.pid):
        completion = completion_times[process.pid]
        turnaround = completion - process.arrival
        waiting = turnaround - process.burst
        metrics.append(
            Metric(
                pid=process.pid,
                arrival=process.arrival,
                burst=process.burst,
                priority=process.priority,
                completion=completion,
                turnaround=turnaround,
                waiting=waiting,
            )
        )

    avg_waiting = sum(metric.waiting for metric in metrics) / len(metrics)
    avg_turnaround = sum(metric.turnaround for metric in metrics) / len(metrics)
    execution_order = [segment.pid for segment in segments if segment.pid != "IDLE"]

    return ScheduleResult(
        algorithm=algorithm,
        segments=segments,
        metrics=metrics,
        avg_waiting=avg_waiting,
        avg_turnaround=avg_turnaround,
        execution_order=execution_order,
    )


def fcfs(processes: List[Process]) -> ScheduleResult:
    """First Come First Serve scheduling, non-preemptive"""
    _validate_processes(processes)
    indexed: List[Tuple[int, Process]] = list(enumerate(processes))
    ready = sorted(indexed, key=lambda item: (item[1].arrival, item[0]))

    current_time = 0
    segments: List[Segment] = []
    completion_times: Dict[str, int] = {}

    for _, process in ready:
        if current_time < process.arrival:
            _merge_or_append(segments, "IDLE", current_time, process.arrival)
            current_time = process.arrival
        start = current_time
        finish = start + process.burst
        _merge_or_append(segments, process.pid, start, finish)
        current_time = finish
        completion_times[process.pid] = finish

    return _build_result("FCFS", processes, segments, completion_times)


def sjf(processes: List[Process]) -> ScheduleResult:
    """Shortest Job First scheduling, non-preemptive"""
    _validate_processes(processes)
    remaining: List[Tuple[int, Process]] = list(enumerate(processes))
    current_time = 0
    segments: List[Segment] = []
    completion_times: Dict[str, int] = {}

    while remaining:
        available = [item for item in remaining if item[1].arrival <= current_time]
        if not available:
            next_arrival = min(item[1].arrival for item in remaining)
            _merge_or_append(segments, "IDLE", current_time, next_arrival)
            current_time = next_arrival
            available = [item for item in remaining if item[1].arrival <= current_time]

        selected_index, selected = min(
            available,
            key=lambda item: (item[1].burst, item[1].arrival, item[0]),
        )
        start = current_time
        finish = start + selected.burst
        _merge_or_append(segments, selected.pid, start, finish)
        completion_times[selected.pid] = finish
        current_time = finish
        remaining.remove((selected_index, selected))

    return _build_result("SJF", processes, segments, completion_times)


def srtf(processes: List[Process]) -> ScheduleResult:
    """Shortest Remaining Time First scheduling, preemptive"""
    _validate_processes(processes)
    indexed: List[Tuple[int, Process]] = list(enumerate(processes))
    remaining_burst: Dict[str, int] = {process.pid: process.burst for process in processes}
    completion_times: Dict[str, int] = {}
    segments: List[Segment] = []
    current_time = 0
    completed = 0

    while completed < len(processes):
        available = [
            item
            for item in indexed
            if item[1].arrival <= current_time and remaining_burst[item[1].pid] > 0
        ]
        if not available:
            next_arrival = min(
                process.arrival
                for process in processes
                if remaining_burst[process.pid] > 0 and process.arrival > current_time
            )
            _merge_or_append(segments, "IDLE", current_time, next_arrival)
            current_time = next_arrival
            continue

        _, selected = min(
            available,
            key=lambda item: (remaining_burst[item[1].pid], item[1].arrival, item[0]),
        )
        start = current_time
        current_time += 1
        remaining_burst[selected.pid] -= 1
        _merge_or_append(segments, selected.pid, start, current_time)

        if remaining_burst[selected.pid] == 0:
            completion_times[selected.pid] = current_time
            completed += 1

    return _build_result("SRTF", processes, segments, completion_times)


def priority_scheduling(processes: List[Process]) -> ScheduleResult:
    """Priority Scheduling, non-preemptive. Lower priority value means higher priority"""
    _validate_processes(processes)
    remaining: List[Tuple[int, Process]] = list(enumerate(processes))
    current_time = 0
    segments: List[Segment] = []
    completion_times: Dict[str, int] = {}

    while remaining:
        available = [item for item in remaining if item[1].arrival <= current_time]
        if not available:
            next_arrival = min(item[1].arrival for item in remaining)
            _merge_or_append(segments, "IDLE", current_time, next_arrival)
            current_time = next_arrival
            available = [item for item in remaining if item[1].arrival <= current_time]

        selected_index, selected = min(
            available,
            key=lambda item: (item[1].priority, item[1].arrival, item[0]),
        )
        start = current_time
        finish = start + selected.burst
        _merge_or_append(segments, selected.pid, start, finish)
        completion_times[selected.pid] = finish
        current_time = finish
        remaining.remove((selected_index, selected))

    return _build_result("Priority", processes, segments, completion_times)


def round_robin(processes: List[Process], quantum: int) -> ScheduleResult:
    """Round Robin scheduling, preemptive"""
    _validate_processes(processes)
    if quantum <= 0:
        raise ValueError("Time quantum must be greater than zero.")

    indexed = sorted(list(enumerate(processes)), key=lambda item: (item[1].arrival, item[0]))
    remaining_burst: Dict[str, int] = {process.pid: process.burst for process in processes}
    completion_times: Dict[str, int] = {}
    ready_queue: deque[Tuple[int, Process]] = deque()
    segments: List[Segment] = []

    current_time = 0
    pointer = 0

    while pointer < len(indexed) or ready_queue:
        if not ready_queue:
            next_arrival = indexed[pointer][1].arrival
            if current_time < next_arrival:
                _merge_or_append(segments, "IDLE", current_time, next_arrival)
                current_time = next_arrival

        while pointer < len(indexed) and indexed[pointer][1].arrival <= current_time:
            ready_queue.append(indexed[pointer])
            pointer += 1

        if not ready_queue:
            continue

        process_index, process = ready_queue.popleft()
        run_time = min(quantum, remaining_burst[process.pid])
        start = current_time
        finish = current_time + run_time
        _merge_or_append(segments, process.pid, start, finish)
        current_time = finish
        remaining_burst[process.pid] -= run_time

        while pointer < len(indexed) and indexed[pointer][1].arrival <= current_time:
            ready_queue.append(indexed[pointer])
            pointer += 1

        if remaining_burst[process.pid] > 0:
            ready_queue.append((process_index, process))
        else:
            completion_times[process.pid] = current_time

    return _build_result(f"Round Robin (q={quantum})", processes, segments, completion_times)


def run_algorithm(processes: List[Process], algorithm: str, quantum: int = 2) -> ScheduleResult:
    normalized = algorithm.strip().lower()
    if normalized == "fcfs":
        return fcfs(processes)
    if normalized == "sjf":
        return sjf(processes)
    if normalized == "srtf":
        return srtf(processes)
    if normalized in {"round robin", "rr"}:
        return round_robin(processes, quantum)
    if normalized in {"priority", "priority scheduling"}:
        return priority_scheduling(processes)
    raise ValueError(f"Unknown algorithm: {algorithm}")


def compare_all(processes: List[Process], quantum: int = 2) -> List[ScheduleResult]:
    return [
        fcfs(processes),
        sjf(processes),
        srtf(processes),
        round_robin(processes, quantum),
        priority_scheduling(processes),
    ]
