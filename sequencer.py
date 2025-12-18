from nimble import NimbleComm
from time import time as now
from math import sin, pi


# Represents a set of toy parameters that should be activated at a specific time
class Params:
    def __init__(self, t, ampl, freq, ampl2, freq2):
        self.t = t              # time [s]
        self.ampl = ampl        # amplitude of the base harmonic
        self.freq = freq        # frequency of the base harmonic
        self.ampl2 = ampl2      # amplitude of the extra harmonic
        self.freq2 = freq2      # frequency of the extra harmonic

    def apply_limit(self):
        tot = self.ampl + self.ampl2
        if tot > 1000:
            scale = 1000 / tot
            self.ampl *= scale
            self.ampl2 *= scale

    def __str__(self):
        return "%4.1f,\ta=%.1f,\tf=%.1f,\ta2=%.1f,\tf2=%.1f" % (self.t, self.ampl, self.freq, self.ampl2, self.freq2)


# A Python generator providing smooth transitions between points
def interpolator(pts):
    t_start = now()
    stage = 0
    while True:
        t = now() - t_start
        if stage < len(pts) - 1:
            p_prev = pts[stage]
            p_next = pts[stage + 1]
            if t > p_next.t:
                stage += 1
            dt = (t - p_prev.t) / (p_next.t - p_prev.t)
        else:
            # if there are no more stages, keep the last preset
            p_prev = pts[stage]
            p_next = pts[stage]
            dt = 0

        # blend two presets
        yield Params(
            t,
            p_prev.ampl + (p_next.ampl - p_prev.ampl) * dt,
            p_prev.freq + (p_next.freq - p_prev.freq) * dt,
            p_prev.ampl2 + (p_next.ampl2 - p_prev.ampl2) * dt,
            p_prev.freq2 + (p_next.freq2 - p_prev.freq2) * dt,
        )


def main():
    # here is a plan of the excitation waveforms
    pts = (
        Params(  0, 100, 1.0,   0, 9),
        Params(180, 500, 1.0,   0, 9),
        Params(240, 500, 3.0,   0, 9),
        Params(300, 500, 3.0, 300, 9),
        Params(360, 500, 3.0, 300, 16),
        Params(420, 500, 4.0, 300, 16),
        Params(480, 500, 4.0, 300, 16),
    )
    interp = interpolator(pts)

    c = NimbleComm()

    t = now()
    t_step = 0.002  # Pendant sends a frame every 2 ms
    t_next = t + t_step
    t_last = t
    t_print = t_next + 1

    # pulsations of the two harmonic signals
    w1 = 0
    w2 = 0
    while True:
        # wait until it's time for a new frame
        while t < t_next:
            t = now()
        t_next += t_step

        # get current setpoint
        pt = next(interp)

        # print current setpoint every second
        if t > t_print:
            t_print += 1
            print(pt)

        # make sure we won't exceed hardware limits
        pt.apply_limit()

        # calculate the time passed from the previous frame
        dt = t - t_last
        t_last = t

        # update signal phases
        dw = 2 * pi * dt
        w1 += pt.freq * dw
        w2 += pt.freq2 * dw

        # generate excitation signal
        pos = int(pt.ampl * sin(w1) + pt.ampl2 * sin(w2))

        # send it to the device
        c.send_pendant_frame(True, position=pos)


if __name__ == '__main__':
    main()