"""Memory Manager - Virtual memory allocation and tracking."""


class MemoryBlock:
    """Represents a memory block."""

    def __init__(self, start, size, pid=None, name=""):
        self.start = start
        self.size = size
        self.pid = pid
        self.name = name
        self.free = pid is None

    def __repr__(self):
        status = "FREE" if self.free else f"PID:{self.pid}"
        return f"MemoryBlock({self.start}-{self.start + self.size}, {self.size}KB, {status})"


class MemoryManager:
    """Manages virtual system memory."""

    def __init__(self, total_mb=8192):
        self.total_kb = total_mb * 1024
        self.blocks = [MemoryBlock(0, self.total_kb)]
        self.allocated = {}
        self.cached_kb = 512 * 1024
        self.buffers_kb = 256 * 1024

    def allocate(self, pid, name, size_kb):
        """Allocate memory for a process."""
        if size_kb <= 0:
            return False, "Invalid size"
        # Find best fit free block
        best_idx = -1
        best_size = float('inf')
        for i, block in enumerate(self.blocks):
            if block.free and block.size >= size_kb:
                if block.size < best_size:
                    best_idx = i
                    best_size = block.size
        if best_idx == -1:
            # Try to free some cached memory
            self.cached_kb = max(0, self.cached_kb - size_kb)
            for i, block in enumerate(self.blocks):
                if block.free and block.size >= size_kb:
                    best_idx = i
                    best_size = block.size
        if best_idx == -1:
            return False, "Out of memory"
        block = self.blocks[best_idx]
        new_block = MemoryBlock(block.start, size_kb, pid, name)
        self.blocks[best_idx] = new_block
        remaining = block.size - size_kb
        if remaining > 0:
            self.blocks.insert(best_idx + 1, MemoryBlock(block.start + size_kb, remaining))
        self.allocated[pid] = self.allocated.get(pid, 0) + size_kb
        return True, ""

    def free(self, pid):
        """Free all memory for a process."""
        freed = 0
        for block in self.blocks:
            if block.pid == pid:
                block.free = True
                block.pid = None
                block.name = ""
                freed += block.size
        if pid in self.allocated:
            del self.allocated[pid]
        self._coalesce()
        return freed

    def _coalesce(self):
        """Merge adjacent free blocks."""
        i = 0
        while i < len(self.blocks) - 1:
            if self.blocks[i].free and self.blocks[i + 1].free:
                self.blocks[i].size += self.blocks[i + 1].size
                self.blocks.pop(i + 1)
            else:
                i += 1

    def get_usage(self):
        """Get memory usage statistics."""
        used = sum(b.size for b in self.blocks if not b.free)
        free = self.total_kb - used
        return {
            "total": self.total_kb,
            "used": used,
            "free": free,
            "cached": self.cached_kb,
            "buffers": self.buffers_kb,
            "usage_percent": (used / self.total_kb) * 100,
        }

    def get_process_memory(self, pid):
        """Get memory allocated to a specific process."""
        return sum(b.size for b in self.blocks if b.pid == pid)

    def get_process_breakdown(self):
        """Get memory breakdown per process."""
        breakdown = {}
        for block in self.blocks:
            if not block.free:
                if block.pid not in breakdown:
                    breakdown[block.pid] = {"name": block.name, "total": 0, "blocks": 0}
                breakdown[block.pid]["total"] += block.size
                breakdown[block.pid]["blocks"] += 1
        return breakdown

    def get_free_memory(self):
        return sum(b.size for b in self.blocks if b.free)

    def get_used_memory(self):
        return sum(b.size for b in self.blocks if not b.free)
