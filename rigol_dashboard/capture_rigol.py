import logging
import time
import io
import socket

from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Literal

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class Datapoints:
    xtick_count: int
    ytick_count: int
    datapoints: int
    x_scale: float  # seconds
    y_scale: float  # volts
    waveform: list[float]


class Commands:
    INSTRUMENT_ID = b"*IDN?"
    SCREENSHOT = b":DISP:DATA?"
    SCREENSHOT_SLOW_PNG = b":DISP:DATA? ON,0,PNG"


class Rigol:
    def __init__(self, ip: IPv4Address):
        self.s = None
        self.ip = ip

    @property
    def datapoints(self) -> int:
        return 100 * self.xtick_count

    @property
    def xtick_count(self) -> int:
        return 12

    @property
    def ytick_count(self) -> int:
        return 8

    @staticmethod
    def _parse_ascii_reply(buf: bytes) -> list[float]:
        assert buf[0] == ord("#")
        _len = buf[1] - ord("0")  # returns a single byt in ascii for len, "9" = 9 bytes
        _header = buf[2 : 2 + _len]
        payload = buf[2 + _len:]  # trailing newline

        return list(map(float, payload.decode().split(",")))

    def connect(self, timeout=0.5):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.ip.exploded, 5555))
        self.s.settimeout(timeout)

    def send_command(self, c: bytes):
        assert self.s is not None
        logger.debug(f"sending {c}")
        start = time.time()
        self.s.sendall(c + b"\n")
        buf = b""
        if b"?" not in c:
            time.sleep(0.02)
            return b""

        while True:
            try:
                buf += self.s.recv(4 * 2**20)
                if buf.endswith(b"\n"):
                    break
            except TimeoutError:
                logger.warning("timeout")
                break

        if not buf:
            logger.error("did not get any data: %s", buf)
            return b""

        end = time.time()
        logger.debug("Capture took", end - start)
        return buf[:-1]

    def take_screenshot(self):
        bmp = self.send_command(Commands.SCREENSHOT)
        assert bmp[0] == ord("B"), bmp[0]
        assert bmp[1] == ord("M")
        assert bmp[2] == ord("6")

        out = io.BytesIO()
        out.write(bmp)
        out.seek(0)

        with Image.open(out) as fd:
            fd.save("out.png", format="png")

    def setup_channel(self, chan: Literal["CHAN1"] | Literal["CHAN2"]):
        logger.debug(self.send_command(f"{chan}:DISP?".encode()))
        logger.debug(self.send_command(b":WAV:MODE NORM"))
        logger.debug(self.send_command(f":WAV:SOUR {chan}".encode()))
        logger.debug(self.send_command(b":WAV:FORM ASC"))  # why ascii

        logger.debug(self.send_command(b":WAV:STAR 1"))
        logger.debug(self.send_command(f":WAV:STOP {self.datapoints}".encode()))

    def capture_channel(self, chan: Literal["CHAN1"] | Literal["CHAN2"]) -> Datapoints:
        yscale = float(self.send_command(f"{chan}:SCAL?".encode()))
        xscale = float(self.send_command(f"TIM:SCAL?".encode()))
        raw_waveform = self.send_command(b":WAV:DATA?")
        if not raw_waveform:
            waveform = []
        else:
            waveform = self._parse_ascii_reply(raw_waveform)

        return Datapoints(
            xtick_count=self.xtick_count,
            ytick_count=self.ytick_count,
            datapoints=1200,
            x_scale=xscale,
            y_scale=yscale,
            waveform=waveform,
        )

    def get_version(self) -> str:
        buf = self.send_command(Commands.INSTRUMENT_ID)
        info = buf.decode().strip()
        return info
