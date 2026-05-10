"""Process Manager - Virtual process creation, scheduling, and management."""
import time
import random


class ProcessState:
    RUNNING = "Running"
    SLEEPING = "Sleeping"
    STOPPED = "Stopped"
    ZOMBIE = "Zombie"


class Process:
    """Represents a virtual process."""

    def __init__(self, pid, name, ppid=1, memory=0):
        self.pid = pid
        self.name = name
        self.ppid = ppid
        self.state = ProcessState.RUNNING
        self.memory = memory
        self.cpu_time = 0.0
        self.start_time = time.time()
        self.priority = 20
        self.nice = 0
        self.threads = 1
        self.user = "root" if pid < 100 else "user"
        self.command = name

    def to_dict(self):
        return {
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "state": self.state,
            "memory": self.memory,
            "cpu_time": self.cpu_time,
            "start_time": time.strftime("%H:%M:%S", time.localtime(self.start_time)),
            "priority": self.priority,
            "nice": self.nice,
            "threads": self.threads,
            "user": self.user,
            "command": self.command,
            "uptime": time.time() - self.start_time,
        }


class ProcessManager:
    """Manages virtual processes."""

    def __init__(self):
        self._processes = {}
        self._next_pid = 1
        self._init_system_processes()

    def _init_system_processes(self):
        """Create initial system processes."""
        system_procs = [
            (1, "init", 0, 4096),
            (2, "kthreadd", 1, 2048),
            (3, "system-monitor", 1, 8192),
            (4, "device-manager", 1, 6144),
            (5, "memory-manager", 1, 4096),
            (6, "fs-sync", 1, 3072),
        ]
        for pid, name, ppid, mem in system_procs:
            proc = Process(pid, name, ppid, mem)
            proc.state = ProcessState.SLEEPING
            self._processes[pid] = proc
            if pid >= self._next_pid:
                self._next_pid = pid + 1

    def create_process(self, name, ppid=100, memory=0):
        """Create a new process."""
        pid = self._next_pid
        self._next_pid += 1
        proc = Process(pid, name, ppid, memory)
        self._processes[pid] = proc
        return proc

    def get_process(self, pid):
        return self._processes.get(pid)

    def get_all_processes(self):
        return list(self._processes.values())

    def get_running_processes(self):
        return [p for p in self._processes.values() if p.state == ProcessState.RUNNING]

    def kill_process(self, pid, signal=9):
        """Kill a process."""
        proc = self._processes.get(pid)
        if proc is None:
            return False, f"kill: ({pid}) - No such process"
        if pid <= 6:
            return False, f"kill: ({pid}) - Operation not permitted (system process)"
        if proc.state == ProcessState.ZOMBIE:
            return False, f"kill: ({pid}) - Process already terminated"
        # Kill children too
        children = [p for p in self._processes.values() if p.ppid == pid]
        for child in children:
            child.state = ProcessState.ZOMBIE
        proc.state = ProcessState.ZOMBIE
        return True, ""

    def stop_process(self, pid):
        proc = self._processes.get(pid)
        if proc is None:
            return False, f"stop: ({pid}) - No such process"
        if pid <= 6:
            return False, f"stop: ({pid}) - Operation not permitted"
        if proc.state == ProcessState.STOPPED:
            return False, f"stop: ({pid}) - Process already stopped"
        proc.state = ProcessState.STOPPED
        return True, ""

    def resume_process(self, pid):
        proc = self._processes.get(pid)
        if proc is None:
            return False, f"resume: ({pid}) - No such process"
        if proc.state == ProcessState.ZOMBIE:
            return False, f"resume: ({pid}) - Process is a zombie"
        proc.state = ProcessState.RUNNING
        return True, ""

    def cleanup_zombies(self):
        """Remove zombie processes."""
        zombies = [pid for pid, p in self._processes.items() if p.state == ProcessState.ZOMBIE]
        for pid in zombies:
            del self._processes[pid]
        return len(zombies)

    def get_process_count(self):
        return len(self._processes)

    def get_total_cpu(self):
        return sum(p.cpu_time for p in self._processes.values())

    def get_total_memory(self):
        return sum(p.memory for p in self._processes.values())

    def update_cpu_times(self):
        """Simulate CPU time progression."""
        for proc in self._processes.values():
            if proc.state == ProcessState.RUNNING:
                proc.cpu_time += random.uniform(0.01, 0.5)
                proc.memory += random.randint(-128, 256)
                if proc.memory < 1024:
                    proc.memory = 1024
