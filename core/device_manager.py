"""Device Manager - Virtual I/O device management."""


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
