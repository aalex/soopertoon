#!/usr/bin/env python
#

"""
if you wont controlls this osc-commands, type this in a python-terminal.

import osc
osc.init()
osc.listen('127.0.0.1', 9951)     # (ip, port)

or DEBUG = True

"""

# defines
DEBUG = False #True

# check with linux the port: 'hwinfo --short'
# first serial = /dev/tty0
serPort = "/dev/ttyUSB0"

import sys, os

from time import sleep

try:
    import threading
except ImportError:
    sys.stderr.write("Error: Modul not found!\npython-threading?\n")
    sys.exit(1)

try:
    import serial
except ImportError:
    sys.stderr.write("Error: Modul not found!\npython-serial?\n")
    sys.exit(1)

try:
    import osc
except ImportError:
    sys.stderr.write("Error: simpleOSC from www.ixi-software.net?\n")
    sys.exit(1)

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except ImportError:
    sys.stderr.write("Error: Modul not found!\npygtk(>2.0)? gtk?\n")
    sys.exit(1)

try:
    import inspect
except ImportError:
    sys.stderr.write("Error: Modul not found!\inspect?\n")


# defaults
default_IP = "localhost"
default_PORT = 9951
default_LOOP = 0
CD_msg = "record"
DSR_msg = "overdub"


all_commands = ["record", "overdub", "multiply", "insert", "replace","reverse",
    "mute", "undo", "redo", "oneshot", "trigger", "substitute", "undo_all",
    "redo_all", "mute_on", "mute_off", "solo", "pause", "solo_next",
    "solo_prev", "record_solo", "record_solo_next", "record_solo_prev",
    "set_sync_pos", "reset_sync_pos"]


def ErrorHandler(error, frame=1):
    """Write the errors in the standard error output.
    In addition, the name of the scripts and the line number"""
    #co = sys._getframe(frame).f_code
    #sys.stderr.write("Frame: %s\n" % co.co_name)
    sys.stderr.write("Error: %s\n" % error)
    if DEBUG:
        stack = inspect.stack()[frame]
        sys.stderr.write("    Frame: %s\n" % stack[3])
        sys.stderr.write("    Line: %d\n" % stack[2])
        sys.stderr.write("    Script: %s\n" % stack[1])


def send_osc(ip = default_IP, port = default_PORT, loop = default_LOOP, command = []):
    """Function, send a list of OSC commands."""
    osc.init()
    bundle = osc.createBundle()
    for item in command:
        osc.appendToBundle(bundle, '/sl/%s/hit' % loop, ['%s' % item])
    osc.sendBundle(bundle, '%s' % ip, int(port))


class Poll(threading.Thread):
    """The player is a thread with a loop for the audio device."""
    def __init__(self):
        self.serialport = self.serial_init()

        threading.Thread.__init__(self)
        self.event_ = threading.Event()
        self.start()
        self.canceled = False

        self.start_()

    def serial_init(self):
        """ initial the serial interface """
        try:
            serialport = serial.Serial(serPort,
                        19200, timeout=1, xonxoff=0, rtscts=0)
        except serial.serialutil.SerialException, e:
            ErrorHandler(e)
            return False
        except IOError, e:
            ErrorHandler(e)
            return False
        return serialport


    def run(self):
        """Method representing the thread's activity."""
        sleep(1)
        x = 0
        y = 0
        while True:
            """Threading"""
            # stop and wait for a event !!!
            self.event_.wait()
            if self.canceled:
                break

            try:
                if self.serialport.getCD():
                    if (x == 0):
                        #print "hit on CD"
                        send_osc(self.box_ip.get_text(),
                                self.box_port.get_text(),
                                self.box_loop.get_text(),
                                [self.box_command1.get_active_text()])
                        x = 1
                else:
                    x = 0

                if self.serialport.getDSR():
                    if (y == 0):
                        #print "hit on DSR"
                        send_osc(self.box_ip.get_text(),
                                self.box_port.get_text(),
                                self.box_loop.get_text(),
                                [self.box_command2.get_active_text()])
                        y = 1
                else:
                    y = 0

            except IOError, e:
                ErrorHandler(e)
                sys.exit(1)
            except AttributeError, e:
                ErrorHandler(e)
                sys.exit(1)

            sleep(0.01)

    def start_(self):
        """set an event to start the thread."""
        self.event_.set()

    def stop_(self):
        """Clear the event to stop the thread."""
        self.event_.clear()

    def quit_(self):
        """Sends a flag to kill the thread."""
        self.canceled = True
        self.event_.set()


class MainWin(Poll):
    """The actual GTk-window."""
    def __init__(self):
        Poll.__init__(self)

        # gtk section
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window_config()
        self.window.show_all()

    def labels(self, x, y, v, w, txt="", bg="white"):
        """dict of all labels"""
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_line_wrap(True)
        event_box = gtk.EventBox()
        event_box.add(label)
        event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bg))
        self.table_.attach(event_box, x, y, v, w)
        label.set_markup("<span foreground='#800000' \
                        weight='normal'>%s</span>" % txt)
        return event_box

    def buttons(self, x, y, v, w, txt="", bg="white"):
        button = gtk.Button(txt)
        button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(bg))
        button.connect("clicked", lambda a: self.callback_start())
        event_box = gtk.EventBox()
        event_box.add(button)
        self.table_.attach(event_box, x, y, v, w)
        return button

    def inputs(self, x, y, v, w, txt="", editor_bg="white", box_bg="white"):
        editor = gtk.Entry()
        editor.set_text(txt)
        editor.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(editor_bg))
        event_box = gtk.EventBox()
        event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(box_bg))
        event_box.add(editor)
        self.table_.attach(event_box, x, y, v, w)
        return editor

    def combos(self, x, y, v, w, commands, sel=0, combo_bg="white", box_bg="white"):
        # list of items to display
        list = gtk.ListStore(str)
        for item in commands:
            iter = list.append((item,))
            list.set(iter)
        combo = gtk.ComboBox()
        combo.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(combo_bg))
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        # we wants to display only the string
        combo.add_attribute(cell, 'text', 0)
        combo.set_model(list)
        combo.set_active(sel)
        #combo.show()
        event_box = gtk.EventBox()
        event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(box_bg))
        event_box.add(combo)
        self.table_.attach(event_box, x, y, v, w)
        return combo

    def window_config(self):
        """Configure the look of window."""

        self.window.set_title("Trampler")
        self.window.connect("destroy", lambda a: self.callback_quit())
        self.window.connect("delete_event", lambda a, b: gtk.main_quit())
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("wheat"))
        self.window.set_border_width(1)
        self.window.set_size_request(200, 180)

        self.table_ = gtk.Table()
        self.table_.resize(6, 8)
        self.table_.set_homogeneous(True)
        self.table_.set_border_width(2)

        # 1. line
        line = 0
        self.box_start = self.buttons(0, 4, line, line + 1, "Start", "#6B8E23")
        self.box_start.connect("clicked", lambda a: self.callback_start())
        self.box_stop = self.buttons(4, 8, line, line + 1, "Stop", "#FF7F50")
        self.box_stop.connect("clicked", lambda a: self.callback_stop())

        # 2. line
        line = line + 1
        # message 'Kabel!'
        if self.serialport:
            self.box = self.labels(0, 5, line, line + 1, "IP-Address", "wheat")
            self.box = self.labels(5, 7, line, line + 1, "Port", "wheat")
            self.box = self.labels(7, 8, line, line + 1, "Lp", "wheat")
        else:
            self.box = self.labels(0, 8, line, line + 1, "No Device!   Kabel?", "white")

        # 3. line
        line = line + 1
        self.box_ip = self.inputs(0, 5, line, line + 1, '%s' % default_IP)
        self.box_port = self.inputs(5, 7, line, line + 1, '%s' % default_PORT)
        self.box_loop = self.inputs(7, 8, line, line + 1, '%s' % default_LOOP)


        # 4. line
        line = line + 1
        self.box = self.labels(0, 4, line, line + 1, "Switch 1", "wheat")
        self.box = self.labels(4, 8, line, line + 1, "Switch 2", "wheat")

        # 5. line
        line = line + 1
        self.box_command1 = self.combos(0, 4, line, line + 1, all_commands, 0)
        self.box_command2 = self.combos(4, 8, line, line + 1, all_commands, 1)

        # 6. line
        line = line + 1
        self.box_cd = self.buttons(0, 4, line, line + 1, "CD", "gray")
        self.box_cd.connect("clicked", lambda a: self.callback_cd())
        self.box_dsr = self.buttons(4, 8, line, line + 1, "DSR", "gray")
        self.box_dsr.connect("clicked", lambda a: self.callback_dsr())

        self.window.add(self.table_)

    def callback_cd(self):
        """The callback for "stop"-button."""
        send_osc(self.box_ip.get_text(),
                self.box_port.get_text(),
                self.box_loop.get_text(),
                [self.box_command1.get_active_text()])

    def callback_dsr(self):
        """The callback for "stop"-button."""
        send_osc(self.box_ip.get_text(),
                self.box_port.get_text(),
                self.box_loop.get_text(),
                [self.box_command2.get_active_text()])

    def callback_stop(self):
        """The callback for "stop"-button."""
        self.stop_()
        self.box_start.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#6B8E23"))

    def callback_start(self):
        """This feature responds to the volume control."""
        self.start_()
        self.box_start.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("orange"))

    def callback_quit(self):
        """The callback for "quit"-button."""
        self.quit_()
        gtk.main_quit()

if __name__ == "__main__":
    win = MainWin()
    if DEBUG:
        osc.init()
        try:
            osc.listen("%s" % win.box_ip.get_text(), int(win.box_port.get_text()))
        except AttributeError, e:
            ErrorHandler(e)
            sys.stderr.write("Maybe the port is already taken by another process?\n")
            sys.stderr.write("SooperLooper is activ?")
    gtk.gdk.threads_init()
    gtk.main() 
