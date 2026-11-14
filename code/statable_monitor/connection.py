"""接続・フレーム送受信（ASCII のみ）。"""
import time

STX = 0x02
ETX = 0x03
CR = 0x0D
MIN_PERIOD_MS = 100
MAX_PERIOD_MS = 60_000


class ConnectionError(Exception):
    pass


class StaTableMonitor:
    def __init__(self, serial_factory=None):
        self._factory = serial_factory
        self._ser = None
        self._timeout = 1.0

    def connect(self, port, baudrate=115200, xml_path=None):
        if self._factory:
            self._ser = self._factory(
                port=port, baudrate=baudrate, timeout=self._timeout)
        else:
            import serial
            self._ser = serial.Serial(port, baudrate, timeout=self._timeout)
        if xml_path:
            self._verify_xml(xml_path)

    def _verify_xml(self, xml_path):
        from .registry import load_xml
        info = load_xml(xml_path)
        pong = self.ping()
        expected = f"{info.crc32:08X}"
        if pong.get("crc") != expected:
            self._ser.close()
            raise ConnectionError(
                f"XML CRC mismatch: xml={expected}, device={pong.get('crc')}")

    def ping(self):
        return self._command("PING")

    def _command(self, body):
        frame = bytes([STX]) + body.encode("ascii") + bytes([CR, ETX])
        self._ser.write(frame)
        return self._parse(self._read_frame())

    def _read_frame(self):
        buf = bytearray()
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            b = self._ser.read(1)
            if not b:
                continue
            if b[0] == STX:
                buf.clear()
                continue
            if b[0] == CR:
                nxt = self._ser.read(1)
                if nxt and nxt[0] == ETX:
                    return buf.decode("ascii", "replace")
                continue
            buf.append(b[0])
        raise TimeoutError("no response")

    @staticmethod
    def _parse(line):
        parts = line.split()
        out = {"kind": parts[0] if parts else "",
               "ret": -1}
        for p in parts[1:]:
            if "=" in p:
                k, v = p.split("=", 1)
                out[k] = v
        if "ret" in out:
            out["ret"] = int(out["ret"])
        return out
