"""Device Manager - Virtual I/O device management."""
import time
import random


class IORequestState:
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class IORequestType:
    READ = "Read"
    WRITE = "Write"
    INPUT = "Input"
    OUTPUT = "Output"


class IORequest:
    """Represents an I/O request to a device."""

    def __init__(self, device_name, request_type, data="", pid=0):
        self.id = random.randint(1000, 9999)
        self.device_name = device_name
        self.request_type = request_type
        self.data = data
        self.pid = pid
        self.state = IORequestState.PENDING
        self.timestamp = time.time()
        self.completed_time = None
        self.result = ""

    def to_dict(self):
        return {
            "id": self.id,
            "device": self.device_name,
            "type": self.request_type,
            "state": self.state,
            "pid": self.pid,
            "timestamp": time.strftime("%H:%M:%S", time.localtime(self.timestamp)),
            "result": self.result,
        }


class IOQueue:
    """Manages I/O requests for all devices."""

    def __init__(self):
        self.pending = []
        self.completed = []
        self.max_history = 50

    def add_request(self, request):
        """Add an I/O request to the pending queue."""
        self.pending.append(request)
        return request

    def process_next(self):
        """Process the next pending I/O request."""
        if not self.pending:
            return None

        req = self.pending[0]
        req.state = IORequestState.PROCESSING

        # Simulate processing (random success/failure)
        success = random.random() < 0.95  # 95% success rate

        if success:
            req.state = IORequestState.COMPLETED
            req.completed_time = time.time()
            if req.request_type == IORequestType.READ:
                req.result = f"Read {len(req.data) if req.data else 0} bytes from {req.device_name}"
            elif req.request_type == IORequestType.WRITE:
                req.result = f"Wrote {len(req.data) if req.data else 0} bytes to {req.device_name}"
            elif req.request_type == IORequestType.INPUT:
                req.result = f"Input received from {req.device_name}"
            elif req.request_type == IORequestType.OUTPUT:
                req.result = f"Output sent to {req.device_name}"
        else:
            req.state = IORequestState.FAILED
            req.completed_time = time.time()
            req.result = f"I/O error on {req.device_name}"

        self.pending.pop(0)
        self.completed.insert(0, req)

        # Trim history
        if len(self.completed) > self.max_history:
            self.completed = self.completed[:self.max_history]

        return req

    def process_all(self):
        """Process all pending requests."""
        processed = []
        while self.pending:
            req = self.process_next()
            if req:
                processed.append(req)
        return processed

    def get_pending_count(self):
        return len(self.pending)

    def get_completed_count(self):
        return len(self.completed)

    def get_requests(self, limit=20):
        """Get recent requests (completed + pending)."""
        return self.completed[:limit] + self.pending


class DeviceState:
    ONLINE = "Online"
    OFFLINE = "Offline"
    ERROR = "Error"
    DISABLED = "Disabled"


class VirtualDevice:
    """Represents a virtual hardware device."""

    def __init__(self, name, category, driver, state=DeviceState.ONLINE):
        self.name = name
        self.category = category
        self.driver = driver
        self.state = state
        self.enabled = True
        self.vendor = "VirtualOS"
        self.bus = "virtual"
        self.properties = {}

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "driver": self.driver,
            "state": self.state,
            "enabled": self.enabled,
            "vendor": self.vendor,
            "bus": self.bus,
            "properties": self.properties,
        }


class DeviceManager:
    """Manages virtual hardware devices."""

    def __init__(self):
        self.devices = []
        self.io_queue = IOQueue()
        self._init_devices()

    def _init_devices(self):
        """Initialize default virtual devices."""
        devices = [
            # CPU
            VirtualDevice("VirtualOS CPU", "Processors", "virt-cpu"),
            VirtualDevice("CPU Core 0", "Processors", "virt-core"),
            VirtualDevice("CPU Core 1", "Processors", "virt-core"),
            VirtualDevice("CPU Core 2", "Processors", "virt-core"),
            VirtualDevice("CPU Core 3", "Processors", "virt-core"),

            # Memory
            VirtualDevice("8GB Virtual RAM", "Memory", "virt-ram"),
            VirtualDevice("Virtual Swap", "Memory", "virt-swap"),

            # Storage
            VirtualDevice("Virtual HDD 256GB", "Disk drives", "virt-disk"),
            VirtualDevice("Virtual SSD 512GB", "Disk drives", "virt-ssd"),
            VirtualDevice("Virtual CD-ROM", "CD/DVD drives", "virt-cdrom"),

            # Display
            VirtualDevice("Virtual Display Adapter", "Display adapters", "virt-gpu"),
            VirtualDevice("Virtual Monitor 1920x1080", "Monitors", "virt-monitor"),

            # Network
            VirtualDevice("Virtual Ethernet Adapter", "Network adapters", "virt-net"),
            VirtualDevice("Virtual WiFi Adapter", "Network adapters", "virt-wifi"),
            VirtualDevice("Virtual Loopback", "Network adapters", "virt-lo"),

            # Input
            VirtualDevice("Virtual Keyboard", "Keyboards", "virt-kbd"),
            VirtualDevice("Virtual Mouse", "Mice", "virt-mouse"),
            VirtualDevice("Virtual Touchpad", "Mice", "virt-touch"),

            # Audio
            VirtualDevice("Virtual Audio Device", "Sound devices", "virt-audio"),
            VirtualDevice("Virtual Microphone", "Sound devices", "virt-mic"),
            VirtualDevice("Virtual Speakers", "Sound devices", "virt-speaker"),

            # USB
            VirtualDevice("Virtual USB Controller", "USB controllers", "virt-usb"),
            VirtualDevice("Virtual USB Hub", "USB controllers", "virt-hub"),

            # System
            VirtualDevice("Virtual BIOS", "System", "virt-bios"),
            VirtualDevice("Virtual ACPI", "System", "virt-acpi"),
            VirtualDevice("Virtual RTC Clock", "System", "virt-rtc"),
            VirtualDevice("Virtual Timer", "System", "virt-timer"),
        ]

        # Add properties
        for dev in devices:
            if "CPU" in dev.name:
                dev.properties = {"MHz": "3600", "Cores": "4", "Architecture": "x86_64"}
            elif "RAM" in dev.name:
                dev.properties = {"Size": "8192 MB", "Speed": "3200 MHz", "Type": "DDR4"}
            elif "HDD" in dev.name or "SSD" in dev.name:
                dev.properties = {"Size": dev.name.split()[-1], "Interface": "SATA III"}
            elif "Display" in dev.name:
                dev.properties = {"VRAM": "256 MB", "Driver Version": "1.0.0"}
            elif "Monitor" in dev.name:
                dev.properties = {"Resolution": "1920x1080", "Refresh Rate": "60 Hz"}
            elif "Ethernet" in dev.name:
                dev.properties = {"MAC": "00:11:22:33:44:55", "Speed": "1000 Mbps"}
            elif "WiFi" in dev.name:
                dev.properties = {"MAC": "AA:BB:CC:DD:EE:FF", "Standard": "802.11ac"}
            elif "Keyboard" in dev.name:
                dev.properties = {"Layout": "US", "Type": "Virtual"}
            elif "Mouse" in dev.name:
                dev.properties = {"Buttons": "5", "DPI": "1600"}
            elif "Audio" in dev.name or "Speaker" in dev.name:
                dev.properties = {"Channels": "Stereo", "Sample Rate": "48000 Hz"}
            elif "BIOS" in dev.name:
                dev.properties = {"Version": "VirtualOS BIOS 1.0", "Date": "2026-01-01"}

        self.devices = devices

    def get_all_devices(self):
        return self.devices

    def get_devices_by_category(self, category):
        return [d for d in self.devices if d.category == category]

    def get_categories(self):
        categories = {}
        for dev in self.devices:
            if dev.category not in categories:
                categories[dev.category] = []
            categories[dev.category].append(dev)
        return categories

    def get_device(self, name):
        for dev in self.devices:
            if dev.name == name:
                return dev
        return None

    def enable_device(self, name):
        dev = self.get_device(name)
        if dev is None:
            return False, f"Device '{name}' not found"
        dev.enabled = True
        dev.state = DeviceState.ONLINE
        return True, ""

    def disable_device(self, name):
        dev = self.get_device(name)
        if dev is None:
            return False, f"Device '{name}' not found"
        dev.enabled = False
        dev.state = DeviceState.DISABLED
        return True, ""

    def get_device_count(self):
        return len(self.devices)

    def get_online_count(self):
        return sum(1 for d in self.devices if d.state == DeviceState.ONLINE)

    def send_io_request(self, device_name, request_type, data="", pid=0):
        """Send an I/O request to a device."""
        dev = self.get_device(device_name)
        if dev is None:
            return False, f"Device '{device_name}' not found"
        if not dev.enabled:
            return False, f"Device '{device_name}' is disabled"
        if dev.state == DeviceState.OFFLINE:
            return False, f"Device '{device_name}' is offline"

        request = IORequest(device_name, request_type, data, pid)
        self.io_queue.add_request(request)
        return True, f"I/O request #{request.id} queued for {device_name}"

    def process_io(self):
        """Process one pending I/O request."""
        return self.io_queue.process_next()

    def process_all_io(self):
        """Process all pending I/O requests."""
        return self.io_queue.process_all()

    def get_io_requests(self, limit=20):
        """Get recent I/O requests."""
        return self.io_queue.get_requests(limit)

    def get_io_pending_count(self):
        return self.io_queue.get_pending_count()
