from serial import Serial
from serial.tools.list_ports import comports
from time import time as now
from math import sin, pi


class NimbleComm:
    def __init__(self, port_name=None):
        self.activated = False
        self.sensor_fault = False
        self.temp_limit = False
        self.air_out = False
        self.air_in = False
        self.air_spring = False
        self.set_exten = False
        self.position = 0
        self.force = 0

        self._port = Serial(port_name, baudrate=115200)
        self._port.timeout = 0.1
        if port_name is None:
            for p in comports():
                if p.hwid.startswith("BTH"):
                    continue
                print("Guessed port: %s" % p.description)
                port_name = p.device
                break
        if port_name is None:
            raise RuntimeError("No suitable COM port found")
        self._port = Serial(port=port_name, baudrate=115200)

    def send_pendant_frame(self, activated, air_out=False, air_in=False, air_spring=False, set_exten=False, position=0, force=1023):
        pos_neg = position < 0
        if pos_neg:
            position = -position
        frm = bytes((
            (1 if activated else 0) | (2 if air_out else 0) | (4 if air_in else 0) | (8 if air_spring else 0) | (16 if set_exten else 0) | 0x80,
            position & 0xFF,
            (4 if pos_neg else 0) | ((position >> 8) & 3),
            force & 0xFF,
            (force >> 8) & 3
        ))
        lrc = sum(frm)
        frm += bytes((lrc & 0xFF, lrc >> 8))
        self._port.write(frm)

    def parse_frame(self, data):
        lrc1 = sum(data[0:5])
        lrc2 = data[5] | (data[6] << 8)
        if lrc1 != lrc2:
            return False

        system_type = data[0] >> 5
        if system_type != 0b100:  # NimbleStroker
            return False

        zeros = data[4] >> 5
        if zeros != 0:
            return False

        node_type = data[2] >> 5
        if node_type == 0b001:  # frame is from the Actuator
            self.activated = (data[0] & 1) != 0
            self.sensor_fault = (data[0] & 2) != 0
            self.temp_limit = (data[0] & 4) != 0
            self.air_spring = (data[0] & 8) != 0
            pos = (data[1] | (data[2] << 8)) & 0x3FF
            if data[2] & 4:
                pos = -pos
            self.position = pos
            frc = (data[3] | (data[4] << 8)) & 0x3FF
            if data[4] & 4:
                frc = -frc
            self.force = frc

        elif node_type == 0b000:  # frame is from the Pendant
            self.activated = (data[0] & 1) != 0
            self.air_out = (data[0] & 2) != 0
            self.air_in = (data[0] & 4) != 0
            self.air_spring = (data[0] & 8) != 0
            self.set_exten = (data[0] & 16) != 0
            pos = (data[1] | (data[2] << 8)) & 0x3FF
            if data[2] & 4:
                pos = -pos
            self.position = pos
            frc = (data[3] | (data[4] << 8)) & 0x3FF
            if data[4] & 4:
                frc = -frc
            self.force = frc

        else:
            return False

        return True

    def read(self, timeout=1):
        t_timeout = now() + timeout
        data = self._port.read(7)
        while not self.parse_frame(data):
            if now() > t_timeout:
                raise TimeoutError("No frame received")
            data = data[1:7] + self._port.read(1)

def demo():
    c = NimbleComm()

    # while True:
    #     c.read()
    #     print(c.activated, c.air_out, c.air_in, c.air_spring, c.set_exten, c.position, c.force)

    t_step = 0.002  # Pendant sends a frame every 2 ms
    t_next = now() + t_step
    while True:
        while now() < t_next:
            pass
        t_next += t_step
        t = now()
        pos = int(500 * sin(t * 2 * 2 * pi) + 300 * sin(t * 2 * 10 * pi))
        c.send_pendant_frame(True, position=pos)


if __name__ == '__main__':
    demo()
