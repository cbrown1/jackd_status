 #!/usr/bin/python3

 #
 # Copyright (C) 2021 Christopher Brown <cbrown1@pitt.edu>
 #
 # This program is free software; you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation; either version 2 of the License, or
 # (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 # GNU General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License along
 # with this program; if not, write to the Free Software Foundation, Inc.,
 # 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 #


"""jackd StatusIcon for the Xfce Panel

    Indicates whether jackd is running, and provides a simple way to start or stop it

    Works with jackd, and not jackdbus

    you must specify the jackd command to use by adding it to the first line of ~/jackd_cmd.txt

    eg, /usr/bin/jackd -P70 -dalsa -r44100 -p1024 -n3 &

    Based on 'StatusIcon test for the Xfce Panel' by Simon Steinbeiß
"""


import sys, os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator
import time
import psutil
import shutil
import threading
import subprocess
import signal


class XfceStatusIcon():

    def __init__(self):

        self.cmd_path = "~/.jackd_cmd.txt"

        if not os.path.exists(os.path.expanduser(self.cmd_path)):
            print(f"Please create the file {self.cmd_path}\nand make sure it contains your jackd startup line")
            raise Exception()

        with open(os.path.expanduser(self.cmd_path)) as f:
            lines = f.readlines()
        self.jack_cmd = lines[0].strip().split(" ")

        self.jack_pid = None
        self.jack_info = None
        self.running = True
        self.timeout = 5

        icon_theme = Gtk.IconTheme.get_default()
        icon_name = "state_shutoff"

        self.indicator = appindicator.Indicator.new(
            "xfce-jack-statusicon",
            icon_name,
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        status_menu = Gtk.Menu()

        self.start_jack_menu_item = Gtk.MenuItem.new_with_label("Start jackd")
        self.start_jack_menu_item.connect("activate", self.jack_toggle_cb)
        status_menu.append(self.start_jack_menu_item)

        quit_menu_item = Gtk.MenuItem.new_with_label("Quit")
        quit_menu_item.connect("activate", self.quit_menu_item_cb)
        status_menu.append(quit_menu_item)

        status_menu.show_all()
        self.indicator.set_menu(status_menu)

        icon_theme.connect('changed', self.icon_theme_changed_cb)

        self.set_status()


    def jack_toggle_cb(self, widget, data=None):
        """Turn jackd on or off

            For turn-on, issue system command from ~/.jackd_cmd.txt
            and wait at most self.timeout sec for it to start

            For turn-off, issue the terminate signal to the jackd pid

        """

        if self.jack_pid and self.jack_pid > -1:
            self.indicator.set_icon_full("state_paused", "Stopping jackd...")
            os.kill(self.jack_pid, signal.SIGTERM)

            start = time.perf_counter()
            wait = True
            while wait:
                if not self.jack_is_running():
                    wait = False
                else:
                    if time.perf_counter() > start + self.timeout:
                        wait = False
                time.sleep(.25)

        else:
            self.indicator.set_icon_full("state_paused", "Starting jackd...")
            po = subprocess.Popen(self.jack_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            start = time.perf_counter()
            wait = True
            while wait:
                if self.jack_is_running():
                    wait = False
                else:
                    if time.perf_counter() > start + self.timeout:
                        wait = False
                time.sleep(.25)


    def jack_is_running(self):
        """Determine if jack daemon is running 

            This looks for the process id of jackd
        """
        try:
            call = subprocess.check_output(f"pidof 'jackd'", shell=True)
            ret = int(call.decode().strip()) # call = b'17283\n'
        except subprocess.CalledProcessError:
            ret = None
        return ret


    def set_status(self):
        """Update status icon & text to indicate jack status

            This function calls itself once per second unless user quits

        """
        ret = self.jack_is_running()
        if ret:
            if not self.jack_info:
                self.jack_info = self.jack_get_info()
            this_info = f"CPU %: {self.jack_cpu()}\n" + self.jack_info
            self.indicator.set_title(f"jackd is running")
            self.indicator.set_icon_full("state_running", this_info)
            self.jack_pid = ret
            self.start_jack_menu_item.set_label("Stop jackd")
        else:
            ret = shutil.which("jackd")
            if ret == "":
                self.indicator.set_title("jackd not found")
                self.indicator.set_icon_full("computer-fail", "Searched path for 'jackd'")
            else:
                self.indicator.set_title("jackd not running")
                self.indicator.set_icon_full("state_shutoff", f"To start Jack, be sure {self.cmd_path}\ncontains your jackd startup command")
            self.jack_pid = None
            self.jack_info = None
            self.start_jack_menu_item.set_label("Start jackd")

        if self.running:
            threading.Timer(1, self.set_status).start()


    def jack_get_info(self):
        """Retrieve some useful jackd parameters 

            This function grabs the command line for the running 
            jackd process and parses it

            I guess argparse would have been better but I didn't 
            think of it until after this was done

        """

        p = psutil.Process(self.jack_pid)
        self.jack_cpu = p.cpu_percent
        cmd = p.cmdline()
        skip = False
        ret = ""
        for i in range(len(cmd)):
            if skip:
                # jackd args can be formatted either as `-r44100` or `-r 44100`
                # skip == True when the prev arg was len==2, which means that the
                # current arg is the value (ie. when the construction is `-r 44100`) 
                # and was already taken (below; `cmd[i+1]`), so don't process this 
                # one and just reset skip to False
                skip = False
            else:
                if cmd[i].startswith("-d"):
                    if len(cmd[i]) == 2:
                        skip = True
                        ret += f"driver: {cmd[i+1]}\n"
                    else:
                        skip = False
                        ret += f"driver: {cmd[i][2:]}\n"
                elif cmd[i].startswith("-r"):
                    if len(cmd[i]) == 2:
                        skip = True
                        ret += f"fs: {cmd[i+1]}\n"
                    else:
                        skip = False
                        ret += f"fs: {cmd[i][2:]}\n"
                elif cmd[i].startswith("-p"):
                    if len(cmd[i]) == 2:
                        skip = True
                        ret += f"frames/period: {cmd[i+1]}\n"
                    else:
                        skip = False
                        ret += f"frames/period: {cmd[i][2:]}\n"
                elif cmd[i].startswith("-n"):
                    if len(cmd[i]) == 2:
                        skip = True
                        ret += f"periods/buffer: {cmd[i+1]}\n"
                    else:
                        skip = False
                        ret += f"periods/buffer: {cmd[i][2:]}\n"

        return (ret.rstrip())


    def icon_theme_changed_cb(self, theme):
        self.update_icon("state_shutoff", "Jack Not Running")


    def quit_menu_item_cb(self, widget, data=None):
        self.running = False
        Gtk.main_quit()


def main():
    try:
        XfceStatusIcon()
        Gtk.main()
    except:
        sys.exit(-1)


if __name__ == '__main__':
    main()