"""Parallel issue scheduler primitives."""

from __future__ import annotations

import ctypes
import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sendsprint.agent_registry import AgentRegistry, default_agent_registry

TaskStatus = Literal["pending", "running", "blocked", "failed", "completed"]


class ScheduledTask(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    issue_key: str
    repo: str
    capability_key: str = "implement"
    status: TaskStatus = "pending"
    provider_key: str | None = None
    confidence: float = 0.5


class HostResourceSnapshot(BaseModel):
    """Host capacity snapshot used to size autonomous fan-out."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    logical_cpus: int = Field(gt=0)
    available_memory_mb: int = Field(ge=0)
    cpu_idle_percent: float | None = Field(default=None, ge=0, le=100)

    @classmethod
    def current(cls) -> HostResourceSnapshot:
        """Return a best-effort local CPU and memory snapshot."""
        return cls(
            logical_cpus=os.cpu_count() or 1,
            available_memory_mb=_available_memory_mb(),
        )


class AgentFanoutPolicy(BaseModel):
    """Resource-aware upper bound for Codex /goal or Ralph worker fan-out."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requested_agents: int = Field(default=5, gt=0)
    max_agents: int = Field(default=12, gt=0)
    reserve_cpus: int = Field(default=2, ge=0)
    reserve_memory_mb: int = Field(default=2048, ge=0)
    memory_mb_per_agent: int = Field(default=1536, gt=0)
    min_cpu_idle_percent: float = Field(default=15.0, ge=0, le=100)

    def limit_for(self, snapshot: HostResourceSnapshot) -> int:
        """Choose a safe concurrent-agent limit from host resources."""
        if (
            snapshot.cpu_idle_percent is not None
            and snapshot.cpu_idle_percent < self.min_cpu_idle_percent
        ):
            return 1

        cpu_slots = max(1, snapshot.logical_cpus - self.reserve_cpus)
        if snapshot.cpu_idle_percent is not None:
            idle_slots = max(
                1,
                int(snapshot.logical_cpus * (snapshot.cpu_idle_percent / 100)),
            )
            cpu_slots = min(cpu_slots, idle_slots)

        if snapshot.available_memory_mb:
            memory_slots = max(
                1,
                (snapshot.available_memory_mb - self.reserve_memory_mb)
                // self.memory_mb_per_agent,
            )
        else:
            memory_slots = self.max_agents

        return max(
            1,
            min(self.requested_agents, self.max_agents, cpu_slots, memory_slots),
        )


class ParallelIssueScheduler(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concurrency_limit: int = 2
    fanout_policy: AgentFanoutPolicy | None = None
    resource_snapshot: HostResourceSnapshot | None = None
    registry: AgentRegistry = Field(default_factory=default_agent_registry)
    tasks: list[ScheduledTask] = Field(default_factory=list)

    def enqueue(self, task: ScheduledTask) -> None:
        self.tasks.append(task)

    @property
    def effective_concurrency_limit(self) -> int:
        if self.fanout_policy is None:
            return self.concurrency_limit
        snapshot = self.resource_snapshot or HostResourceSnapshot.current()
        return self.fanout_policy.limit_for(snapshot)

    def dispatchable(self) -> list[ScheduledTask]:
        running = sum(1 for task in self.tasks if task.status == "running")
        capacity = max(0, self.effective_concurrency_limit - running)
        ready = [task for task in self.tasks if task.status == "pending"]
        return ready[:capacity]

    def assign_next(self) -> list[ScheduledTask]:
        assigned: list[ScheduledTask] = []
        for task in self.dispatchable():
            provider = self.registry.preferred_provider_for(task.capability_key)
            if provider is None:
                self._replace(task, status="blocked")
                continue
            assigned_task = task.model_copy(
                update={"provider_key": provider.key, "status": "running"}
            )
            self._replace(assigned_task)
            assigned.append(assigned_task)
        return assigned

    def _replace(self, updated: ScheduledTask, **changes: str) -> None:
        replacement = updated.model_copy(update=changes) if changes else updated
        self.tasks = [
            replacement
            if task.issue_key == updated.issue_key and task.repo == updated.repo
            else task
            for task in self.tasks
        ]


def _available_memory_mb() -> int:
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullAvailPhys // (1024 * 1024))
        return 0

    if hasattr(os, "sysconf"):
        page_size = os.sysconf("SC_PAGE_SIZE")
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
        return int((page_size * available_pages) // (1024 * 1024))

    return 0
