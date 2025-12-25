#!/usr/bin/python3

import tkinter as tk
import tkinter.ttk as ttk
from time import time as now
from threading import Thread, Event
from math import sin, pi
from nimble import NimbleComm


class Slider(ttk.Frame):
    def __init__(self, master, name, range_min, range_max, format="%0.1f"):
        super().__init__(master)
        self.value = range_min
        self.format = format

        self.name_lbl = ttk.Label(self, text=name)
        self.name_lbl.place(relx=0, rely=0.1, relwidth=1.0, relheight=0.4, bordermode='ignore')

        self.value_lbl = ttk.Label(self)
        self.value_lbl.place(relx=0.85, rely=0.5, relwidth=0.15, relheight=0.4, bordermode='ignore')

        self.scale = ttk.Scale(self, from_=range_min, to=range_max, command=self.value_changed)
        self.scale.place(relx=0.0, rely=0.5, relwidth=0.8, relheight=0.4)
        self.scale.set(self.value)

    def value_changed(self, value):
        self.value = float(value)
        self.value_lbl.configure(text=self.format % self.value)


class ExcitationControl(ttk.LabelFrame):
    def __init__(self, master, name):
        super().__init__(master)
        self.configure(text=name)

        self.ampl = Slider(self, "Amplitude", 0, 1000, "%.0f")
        self.ampl.place(relx=0.05, rely=0.15, relheight=0.35, relwidth=0.9, bordermode='ignore')

        self.freq = Slider(self, "Frequency", 0.1, 20, "%.1f Hz")
        self.freq.place(relx=0.05, rely=0.55, relheight=0.35, relwidth=0.9, bordermode='ignore')


class PressureControl(ttk.LabelFrame):
    def __init__(self, master, name):
        super().__init__(master, text=name)
        self.inflate = False
        self.deflate = False
        self.air_spring = False

        self.btn_up = ttk.Button(self, text="Up", command=self.up)
        self.btn_up.place(relx=0.1, rely=0.3, relwidth=0.15, relheight=0.6, bordermode='ignore')

        self.btn_down = ttk.Button(self, text="Stop", command=self.stop)
        self.btn_down.place(relx=0.3, rely=0.3, relwidth=0.15, relheight=0.6, bordermode='ignore')

        self.btn_spring = ttk.Button(self, text="Down", command=self.down)
        self.btn_spring.place(relx=0.5, rely=0.3, relwidth=0.15, relheight=0.6, bordermode='ignore')

        self.lbl = ttk.Label(self)
        self.lbl.place(relx=0.7, rely=0.3, relwidth=0.2, relheight=0.6, bordermode='ignore')

    def up(self):
        if self.inflate:
            self.stop()
            return
        self.inflate = True
        self.deflate = False
        self.lbl.configure(text="Inflating")

    def stop(self):
        self.inflate = False
        self.deflate = False
        self.lbl.configure(text="")

    def down(self):
        if self.deflate:
            self.stop()
            return
        self.inflate = False
        self.deflate = True
        self.lbl.configure(text="Deflating")


class MainWindow:
    def __init__(self, top=None):

        top.geometry("600x600")
        top.resizable(1,  1)
        top.title("NimbleStroker Control Panel")

        self.e1 = ExcitationControl(top, "Base Excitation")
        self.e1.place(relx=0.1, rely=0.075, relwidth=0.8, relheight=0.3, bordermode='ignore')

        self.e2 = ExcitationControl(top, "Extra Excitation")
        self.e2.place(relx=0.1, rely=0.45, relwidth=0.8, relheight=0.3, bordermode='ignore')

        self.pc = PressureControl(top, "Pressure Control")
        self.pc.place(relx=0.1, rely=0.825, relwidth=0.8, relheight=0.1, bordermode='ignore')


def comm_thread(e: Event, w: MainWindow, c: NimbleComm):
    t = now()
    t_step = 0.002  # Pendant sends a frame every 2 ms
    t_next = t + t_step
    t_last = t

    # pulsations of the two harmonic signals
    w1 = 0
    w2 = 0

    while not e.is_set():
        # wait until it's time for a new frame
        while t < t_next:
            t = now()
        t_next += t_step

        # calculate the time passed from the previous frame
        dt = t - t_last
        t_last = t

        a1, a2, f1, f2 = w.e1.ampl.value, w.e2.ampl.value, w.e1.freq.value, w.e2.freq.value

        # make sure we won't exceed hardware limits
        pwr = (a1 + a2) / 1000
        if pwr > 1.0:
            a1 /= pwr
            a2 /= pwr

        # update signal phases
        dw = 2 * pi * dt
        w1 += f1 * dw
        w2 += f2 * dw

        # generate excitation signal
        pos = int(a1 * sin(w1) + a2 * sin(w2))

        # send it to the device
        c.send_pendant_frame(True, position=pos, air_in=w.pc.inflate, air_out=w.pc.deflate)


def main():
    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', root.destroy)
    w = MainWindow(root)
    e = Event()
    c = NimbleComm()
    th = Thread(target=comm_thread, args=(e, w, c))
    th.start()
    try:
        root.mainloop()
    finally:
        e.set()
        th.join()


if __name__ == "__main__":
    main()
