import time
import ctypes
from ctypes import wintypes

class NET_LUID(ctypes.Structure):
    _fields_ = [('Value', ctypes.c_uint64)]

class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', wintypes.DWORD),
        ('Data2', wintypes.WORD),
        ('Data3', wintypes.WORD),
        ('Data4', wintypes.BYTE * 8)
    ]

class MIB_IF_ROW2(ctypes.Structure):
    _fields_ = [
        ('InterfaceLuid', NET_LUID),
        ('InterfaceIndex', wintypes.DWORD),
        ('InterfaceGuid', GUID),
        ('Alias', wintypes.WCHAR * 257),
        ('Description', wintypes.WCHAR * 257),
        ('PhysicalAddressLength', wintypes.DWORD),
        ('PhysicalAddress', wintypes.BYTE * 32),
        ('PermanentPhysicalAddress', wintypes.BYTE * 32),
        ('Mtu', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TunnelType', wintypes.DWORD),
        ('MediaType', wintypes.DWORD),
        ('PhysicalMediumType', wintypes.DWORD),
        ('AccessType', wintypes.DWORD),
        ('DirectionType', wintypes.DWORD),
        ('InterfaceAndOperStatusFlags', wintypes.BYTE),
        ('OperStatus', wintypes.DWORD),
        ('AdminStatus', wintypes.DWORD),
        ('MediaConnectState', wintypes.DWORD),
        ('NetworkGuid', GUID),
        ('ConnectionType', wintypes.DWORD),
        ('TransmitLinkSpeed', ctypes.c_uint64),
        ('ReceiveLinkSpeed', ctypes.c_uint64),
        ('InOctets', ctypes.c_uint64),
        ('InUcastPkts', ctypes.c_uint64),
        ('InNUcastPkts', ctypes.c_uint64),
        ('InDiscards', ctypes.c_uint64),
        ('InErrors', ctypes.c_uint64),
        ('InUnknownProtos', ctypes.c_uint64),
        ('InUcastOctets', ctypes.c_uint64),
        ('InMulticastOctets', ctypes.c_uint64),
        ('InBroadcastOctets', ctypes.c_uint64),
        ('OutOctets', ctypes.c_uint64),
    ]

class MIB_IF_TABLE2(ctypes.Structure):
    _fields_ = [('NumEntries', wintypes.ULONG), ('Table', MIB_IF_ROW2 * 1)]

def _get_active_interface_octets():
    """Returns total (in_octets, out_octets) for active Ethernet & Wi-Fi adapters in 0.05ms."""
    try:
        iphlpapi = ctypes.windll.iphlpapi
        pTable = ctypes.POINTER(MIB_IF_TABLE2)()
        res = iphlpapi.GetIfTable2(ctypes.byref(pTable))
        if res == 0:
            try:
                num = pTable.contents.NumEntries
                class ACTUAL_TABLE(ctypes.Structure):
                    _fields_ = [('NumEntries', wintypes.ULONG), ('Table', MIB_IF_ROW2 * num)]
                act = ctypes.cast(pTable, ctypes.POINTER(ACTUAL_TABLE)).contents
                tot_in = 0
                tot_out = 0
                for i in range(num):
                    row = act.Table[i]
                    # OperStatus 1 = Up, Type 6 = Ethernet, Type 71 = 802.11 Wi-Fi
                    if row.OperStatus == 1 and row.Type in (6, 71):
                        tot_in += int(row.InOctets)
                        tot_out += int(row.OutOctets)
                return tot_in, tot_out
            finally:
                iphlpapi.FreeMibTable(pTable)
    except Exception:
        pass
    return 0, 0

class SessionStats:
    def __init__(self):
        self.is_active = False
        self.start_timestamp = 0
        self.baseline_in = 0
        self.baseline_out = 0
        self.last_in = 0
        self.last_out = 0
        self.last_poll_time = 0
        self.session_bytes = 0
        self.current_speed_mbps = 0.0
        self.peak_speed_mbps = 0.0

    def start(self):
        tot_in, tot_out = _get_active_interface_octets()
        self.is_active = True
        self.start_timestamp = time.time()
        self.baseline_in = tot_in
        self.baseline_out = tot_out
        self.last_in = tot_in
        self.last_out = tot_out
        self.last_poll_time = time.time()
        self.session_bytes = 0
        self.current_speed_mbps = 0.0
        self.peak_speed_mbps = 0.0

    def stop(self):
        self.is_active = False
        self.current_speed_mbps = 0.0

    def update(self):
        if not self.is_active:
            return

        now = time.time()
        tot_in, tot_out = _get_active_interface_octets()

        # Cumulative session transfer
        if tot_in >= self.baseline_in and tot_out >= self.baseline_out:
            self.session_bytes = (tot_in - self.baseline_in) + (tot_out - self.baseline_out)

        # Delta speed computation
        dt = now - self.last_poll_time
        if dt >= 0.8:
            delta_in = max(0, tot_in - self.last_in)
            delta_out = max(0, tot_out - self.last_out)
            delta_bytes = delta_in + delta_out
            
            # Bits per second to Mbps
            speed_mbps = round((delta_bytes * 8.0) / (dt * 1_000_000.0), 1)
            self.current_speed_mbps = speed_mbps
            if speed_mbps > self.peak_speed_mbps:
                self.peak_speed_mbps = speed_mbps

            self.last_in = tot_in
            self.last_out = tot_out
            self.last_poll_time = now

    def record_manual_speed(self, speed_mbps):
        """Called when YouTube stream benchmark completes."""
        try:
            val = float(speed_mbps)
            if val > self.peak_speed_mbps:
                self.peak_speed_mbps = val
        except Exception:
            pass

    def get_uptime_formatted(self):
        if not self.is_active or self.start_timestamp == 0:
            return "00:00:00"
        elapsed = int(time.time() - self.start_timestamp)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    def get_traffic_formatted(self):
        mb = self.session_bytes / (1024.0 * 1024.0)
        if mb >= 1024.0:
            gb = mb / 1024.0
            return f"{gb:.2f} ГБ"
        return f"{mb:.1f} МБ"

    def get_speed_formatted(self):
        return f"{self.current_speed_mbps:.1f} Мбит/с"

    def get_peak_formatted(self):
        return f"{self.peak_speed_mbps:.1f} Мбит/с"

# Global session stats instance
session_stats = SessionStats()
