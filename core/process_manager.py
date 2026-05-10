"""Process Manager - Virtual process creation, scheduling, and management."""
import time
import random


class ProcessState:
    RUNNING = "Running"
    READY = "Ready"
    WAITING = "Waiting"
    SLEEPING = "Sleeping"
    STOPPED = "Stopped"
    ZOMBIE = "Zombie"


class RoundRobinScheduler:
    """Simple Round-Robin CPU scheduler."""

    def __init__(self, time_quantum=3.0):
        self.time_quantum = time_quantum
        self.ready_queue = []
        self.current_pid = None
        self._elapsed = 0.0

    def add_process(self, proc):
        """Add a process to the ready queue."""
        if proc not in self.ready_queue and proc.state == ProcessState.READY:
            self.ready_queue.append(proc)

    def remove_process(self, pid):
        """Remove a process from the ready queue."""
        self.ready_queue = [p for p in self.ready_queue if p.pid != pid]
        if self.current_pid == pid:
            self.current_pid = None

    def schedule(self, processes):
        """Run one scheduling cycle. Rotate processes and manage states."""
        runnable = [p for p in processes if p.state == ProcessState.RUNNING]

        if not runnable:
            # Promote ready processes to running
            promoted = []
            for proc in list(self.ready_queue):
                proc.state = ProcessState.RUNNING
                promoted.append(proc)
            self.ready_queue = []
            if promoted:
                self.current_pid = promoted[0].pid
            return

        self._elapsed += 0.1  # simulated 100ms tick

        # Time quantum check — rotate if exceeded
        if self._elapsed >= self.time_quantum:
            self._elapsed = 0.0
            current = next((p for p in runnable if p.pid == self.current_pid), None)
            if current:
                # Move current process to back of ready queue
                current.state = ProcessState.READY
                self.ready_queue.append(current)
            # Promote next ready process
            if self.ready_queue:
                next_proc = self.ready_queue.pop(0)
                next_proc.state = ProcessState.RUNNING
                self.current_pid = next_proc.pid
            elif len(runnable) > 1:
                # Rotate among running
                idx = next((i for i, p in enumerate(runnable) if p.pid == self.current_pid), -1)
                if idx >= 0:
                    next_idx = (idx + 1) % len(runnable)
                    self.current_pid = runnable[next_idx].pid


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
        self.scheduler = RoundRobinScheduler()
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
        proc.state = ProcessState.READY
        self._processes[pid] = proc
        self.scheduler.add_process(proc)
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
        if proc.state == ProcessState.ZOMBIE:
            return False, f"kill: ({pid}) - Process already terminated"
        # Kill children too
        children = [p for p in self._processes.values() if p.ppid == pid]
        for child in children:
            child.state = ProcessState.ZOMBIE
            self.scheduler.remove_process(child.pid)
        proc.state = ProcessState.ZOMBIE
        self.scheduler.remove_process(pid)
        return True, ""

    def stop_process(self, pid):
        proc = self._processes.get(pid)
        if proc is None:
            return False, f"stop: ({pid}) - No such process"
        if proc.state == ProcessState.STOPPED:
            return False, f"stop: ({pid}) - Process already stopped"
        if proc.state == ProcessState.ZOMBIE:
            return False, f"stop: ({pid}) - Process is a zombie"
        self.scheduler.remove_process(pid)
        proc.state = ProcessState.STOPPED
        return True, ""

    def resume_process(self, pid):
        proc = self._processes.get(pid)
        if proc is None:
            return False, f"resume: ({pid}) - No such process"
        if proc.state == ProcessState.ZOMBIE:
            return False, f"resume: ({pid}) - Process is a zombie"
        proc.state = ProcessState.READY
        self.scheduler.add_process(proc)
        return True, ""

    def cleanup_zombies(self):
        """Remove zombie processes."""
        zombies = [pid for pid, p in self._processes.items() if p.state == ProcessState.ZOMBIE]
        for pid in zombies:
            del self._processes[pid]
        return len(zombies)

    def schedule(self):
        """Run the Round-Robin scheduler."""
        self.scheduler.schedule(list(self._processes.values()))

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
