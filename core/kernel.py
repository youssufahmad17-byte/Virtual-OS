"""Kernel - Central coordinator for all virtual OS subsystems."""
import time
from core.filesystem import VirtualFS
from core.process_manager import ProcessManager
from core.memory_manager import MemoryManager
from core.device_manager import DeviceManager


class Kernel:
    """Central kernel coordinating all subsystems."""

    def __init__(self):
        self.filesystem = VirtualFS()
        self.process_manager = ProcessManager()
        self.memory_manager = MemoryManager(total_mb=8192)
        self.device_manager = DeviceManager()
        self.boot_time = time.time()
        self.hostname = "virtual-os"
        self.kernel_version = "VirtualOS 1.0.0"
        self.os_name = "VirtualOS"
        self.os_version = "1.0"

        # Allocate memory for system processes
        for proc in self.process_manager.get_all_processes():
            self.memory_manager.allocate(proc.pid, proc.name, proc.memory)

    def get_uptime(self):
        elapsed = time.time() - self.boot_time
        days = int(elapsed // 86400)
        hours = int((elapsed % 86400) // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        if days > 0:
            return f"{days} day(s), {hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_system_info(self):
        return {
            "os": self.os_name,
            "version": self.os_version,
            "kernel": self.kernel_version,
            "hostname": self.hostname,
            "uptime": self.get_uptime(),
            "processes": self.process_manager.get_process_count(),
            "memory_total": f"{self.memory_manager.total_kb // 1024} MB",
            "memory_used": f"{self.memory_manager.get_used_memory() // 1024} MB",
            "memory_free": f"{self.memory_manager.get_free_memory() // 1024} MB",
            "devices": self.device_manager.get_device_count(),
            "devices_online": self.device_manager.get_online_count(),
        }

    def update(self):
        """Called periodically to update system state."""
        self.process_manager.update_cpu_times()
        self.process_manager.cleanup_zombies()
