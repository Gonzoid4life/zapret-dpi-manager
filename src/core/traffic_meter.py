import ctypes
import time
from ctypes import wintypes

class MIB_IF_ROW2(ctypes.Structure):
    _fields_ = [
        ("InterfaceLuid", ctypes.c_uint64),
        ("InterfaceIndex", wintypes.DWORD),
        ("InterfaceGuid", ctypes.c_byte * 16),
        ("Alias", wintypes.WCHAR * 257),
        ("Description", wintypes.WCHAR * 257),
        ("PhysicalAddressLength", wintypes.DWORD),
        ("PhysicalAddress", ctypes.c_byte * 32),
        ("PermanentPhysicalAddress", ctypes.c_byte * 32),
        ("Mtu", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TunnelType", wintypes.DWORD),
        ("MediaType", wintypes.DWORD),
        ("PhysicalMediumType", wintypes.DWORD),
        ("AccessType", wintypes.DWORD),
        ("DirectionType", wintypes.DWORD),
        ("InterfaceAndOperStatusFlags", ctypes.c_byte * 4),
        ("OperStatus", wintypes.DWORD),
        ("AdminStatus", wintypes.DWORD),
        ("MediaConnectState", wintypes.DWORD),
        ("NetworkGuid", ctypes.c_byte * 16),
        ("ConnectionType", wintypes.DWORD),
        ("TransmitLinkSpeed", ctypes.c_uint64),
        ("ReceiveLinkSpeed", ctypes.c_uint64),
        ("InOctets", ctypes.c_uint64),
        ("InUcastPkts", ctypes.c_uint64),
        ("InNUcastPkts", ctypes.c_uint64),
        ("InDiscards", ctypes.c_uint64),
        ("InErrors", ctypes.c_uint64),
        ("InUnknownProtos", ctypes.c_uint64),
        ("InUcastOctets", ctypes.c_uint64),
        ("InMulticastOctets", ctypes.c_uint64),
        ("InBroadcastOctets", ctypes.c_uint64),
        ("OutOctets", ctypes.c_uint64),
        ("OutUcastPkts", ctypes.c_uint64),
        ("OutNUcastPkts", ctypes.c_uint64),
        ("OutDiscards", ctypes.c_uint64),
        ("OutErrors", ctypes.c_uint64),
        ("OutUcastOctets", ctypes.c_uint64),
        ("OutMulticastOctets", ctypes.c_uint64),
        ("OutBroadcastOctets", ctypes.c_uint64),
        ("OutQLen", ctypes.c_uint64)
    ]

class MIB_IF_TABLE2(ctypes.Structure):
    _fields_ = [
        ("NumEntries", wintypes.ULONG),
        ("Table", MIB_IF_ROW2 * 1)
    ]

class TrafficMeter:
    def __init__(self):
        self.last_in_bytes = 0
        self.last_out_bytes = 0
        self.last_time = 0
        self.iphlpapi = ctypes.windll.iphlpapi
        try:
            self.iphlpapi.GetIfTable2.argtypes = [ctypes.POINTER(ctypes.POINTER(MIB_IF_TABLE2))]
            self.iphlpapi.GetIfTable2.restype = wintypes.ULONG
            self.iphlpapi.FreeMibTable.argtypes = [ctypes.c_void_p]
            self.iphlpapi.FreeMibTable.restype = None
        except Exception:
            pass
        self.reset()

    def _query_octets(self):
        p_table = None
        try:
            p_table = ctypes.POINTER(MIB_IF_TABLE2)()
            ret = self.iphlpapi.GetIfTable2(ctypes.byref(p_table))
            if ret != 0 or not p_table:
                return 0, 0

            entries = p_table.contents.NumEntries
            row_array = ctypes.cast(
                ctypes.addressof(p_table.contents.Table),
                ctypes.POINTER(MIB_IF_ROW2 * entries)
            ).contents

            total_in = 0
            total_out = 0
            for row in row_array:
                # 6 = Ethernet, 71 = 802.11 WiFi, 23 = PPP, 24 = Loopback (skip loopback)
                if row.Type != 24 and row.OperStatus == 1:  # IfOperStatusUp = 1
                    total_in += row.InOctets
                    total_out += row.OutOctets

            return total_in, total_out
        except Exception:
            return 0, 0
        finally:
            if p_table:
                try:
                    self.iphlpapi.FreeMibTable(p_table)
                except Exception:
                    pass

    def reset(self):
        in_b, out_b = self._query_octets()
        self.last_in_bytes = in_b
        self.last_out_bytes = out_b
        self.last_time = time.time()

    def get_speed(self):
        """
        Returns:
            down_mbps (float),
            up_mbps (float),
            formatted_str (str)
        """
        now = time.time()
        in_b, out_b = self._query_octets()

        time_delta = now - self.last_time
        if time_delta <= 0:
            time_delta = 1.0

        if self.last_in_bytes == 0:
            self.last_in_bytes = in_b
            self.last_out_bytes = out_b
            self.last_time = now
            return 0.0, 0.0, "⚡ 0 КБ/с"

        diff_in = max(0, in_b - self.last_in_bytes)
        diff_out = max(0, out_b - self.last_out_bytes)

        self.last_in_bytes = in_b
        self.last_out_bytes = out_b
        self.last_time = now

        bytes_per_sec_in = diff_in / time_delta
        bytes_per_sec_out = diff_out / time_delta

        mbps_in = (bytes_per_sec_in * 8) / 1_000_000

        # Human-readable formatting
        if bytes_per_sec_in >= 1_048_576:
            down_str = f"{bytes_per_sec_in / 1_048_576:.1f} МБ/с"
        elif bytes_per_sec_in >= 1024:
            down_str = f"{bytes_per_sec_in / 1024:.0f} КБ/с"
        else:
            down_str = "0 КБ/с"

        if mbps_in >= 1.0:
            formatted = f"⚡ {mbps_in:.1f} Мбит/с  (▼ {down_str})"
        elif bytes_per_sec_in > 1024:
            formatted = f"⚡ ▼ {down_str}"
        else:
            formatted = "⚡ 0 КБ/с"

        return mbps_in, (bytes_per_sec_out * 8) / 1_000_000, formatted
