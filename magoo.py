"""Magoo A bot to pilot the Spacex iss-sim webgl application at iss-sim.spacex.com

@author: James A. Feister
@email: openjaf@gmail.com

For now creates a webkit instance and a bot to pilot the iss craft ('webgl') camera within the iss-sim simulation.


I think the framework for the web application originated from https://gist.github.com/pydoh/2f1b8287276bb70d961e88842ebe741f

The intent is to generalize this automation to other webpages.
"""
import sys
import time
import threading

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, GLib, Gdk, WebKit2


# rateCurrent
# rateRotationX     # Pitch Speed
# rateRotationY     # Yaw Speed
# rateRotationZ     # Roll Speed
# fixedRotationX    # Pitch
# fixedRotationY    # Yaw
# fixedRotationZ    # Roll
# rateCurrent       # Velocity
# camera.position.z - issObject.position.z      # X
# camera.position.x - issObject.position.x      # Y
# camera.position.y - issObject.position.y      # Z

class DumbBot:
    """A very very dumb bot to pilot the craft.  Do not trust it."""
    def __init__(self, browser_window):
        self.run_bot = False
        self.thread_handle = threading.Thread(target=self.main_thread)
        self.thread_handle.daemon = True
        self.browser_window = browser_window

    def main_thread(self):
        self.run_bot = True

        translation_tick = 0
        translation_tick_slice = 100
        orientation_tick = 0
        orientation_tick_slice = 50

        print("Starting Bot")
        while self.run_bot:
            GLib.idle_add(self.browser_window.query_craft_values)
            if orientation_tick % orientation_tick_slice == 0:
                # Pitch
                if self.browser_window.get_fixed_rotation_x() > 0 and self.browser_window.get_rate_rotation_x() < (
                        min(abs(self.browser_window.get_fixed_rotation_x()), 1) * 2):
                    GLib.idle_add(self.browser_window.pitch_down)
                if self.browser_window.get_fixed_rotation_x() < 0 and self.browser_window.get_rate_rotation_x() > (
                        min(abs(self.browser_window.get_fixed_rotation_x()), 1) * -2):
                    GLib.idle_add(self.browser_window.pitch_up)
                # Yaw
                if self.browser_window.get_fixed_rotation_y() > 0 and self.browser_window.get_rate_rotation_y() < (
                        min(abs(self.browser_window.get_fixed_rotation_y()), 1) * 2):
                    GLib.idle_add(self.browser_window.yaw_right)
                if self.browser_window.get_fixed_rotation_y() < 0 and self.browser_window.get_rate_rotation_y() > (
                        min(abs(self.browser_window.get_fixed_rotation_y()), 1) * -2):
                    GLib.idle_add(self.browser_window.yaw_left)
                # Roll
                if self.browser_window.get_fixed_rotation_z() > 0 and self.browser_window.get_rate_rotation_z() < (
                        min(abs(self.browser_window.get_fixed_rotation_z()), 1) * 2):
                    GLib.idle_add(self.browser_window.roll_right)
                if self.browser_window.get_fixed_rotation_z() < 0 and self.browser_window.get_rate_rotation_z()> (
                        min(abs(self.browser_window.get_fixed_rotation_z()), 1) * -2):
                    GLib.idle_add(self.browser_window.roll_left)

            if translation_tick % translation_tick_slice == 0:
                # Translate X
                if self.browser_window.get_translation_y() < 0:
                    GLib.idle_add(self.browser_window.translate_right)
                if self.browser_window.get_translation_y() > 0:
                    GLib.idle_add(self.browser_window.translate_left)
                # Translate Z
                if self.browser_window.get_translation_z() < 0:
                    GLib.idle_add(self.browser_window.translate_up)
                if self.browser_window.get_translation_z() > 0:
                    GLib.idle_add(self.browser_window.translate_down)

            orientation_tick += 1
            translation_tick += 1
            time.sleep(0.01)
        print("Bot Loop Stopped.")

    def start(self):
        self.thread_handle.start()

    def stop(self):
        self.run_bot = False


class ISSSimTab(Gtk.VBox):
    def __init__(self, *args, **kwargs):
        super(ISSSimTab, self).__init__(*args, **kwargs)

        self.fixedRotationX = [0]  # Pitch
        self.fixedRotationY = [0]  # Yaw
        self.fixedRotationZ = [0]  # Roll
        self.rateCurrent = [0]  # Velocity
        self.rateRotationX = [0]  # Pitch Speed
        self.rateRotationY = [0]  # Yaw Speed
        self.rateRotationZ = [0]  # Roll Speed
        self.x = [0]  # camera.position.z - issObject.position.z      # X
        self.z = [0]  # camera.position.y - issObject.position.y      # Z
        self.y = [0]  # camera.position.x - issObject.position.x      # Y
        self.rollLeft_javascript = "rollLeft()"
        self.rollRight_javascript = "rollRight()"
        self.pitchDown_javascript = "pitchDown()"
        self.pitchUp_javascript = "pitchUp()"
        self.yawLeft_javascript = "yawLeft()"
        self.yawRight_javascript = "yawRight()"
        self.translateForward_javascript = "translateForward()"
        self.translateBackward_javascript = "translateBackward()"
        self.translateDown_javascript = "translateDown()"
        self.translateUp_javascript = "translateUp()"
        self.translateRight_javascript = "translateRight()"
        self.translateLeft_javascript = "translateLeft()"
        self.bot = DumbBot(self)

        self.webview = WebKit2.WebView()
        self.show()

        self.get_bot_values_button = Gtk.Button.new_with_label("Get Bot Values")
        self.get_bot_values_button.connect("clicked", lambda x: self.query_craft_values())
        self.print_bot_values_button = Gtk.Button.new_with_label("Print Bot Values")
        self.print_bot_values_button.connect("clicked", lambda x: self.print_craft_values())
        self.run_bot_button = Gtk.Button.new_with_label("Run Bot")
        self.stop_bot_button = Gtk.Button.new_with_label("Stop Bot")
        self.create_bot_button = Gtk.Button.new_with_label("Create Bot")
        self.run_bot_button.connect("clicked", lambda x: self.start_bot())
        self.stop_bot_button.connect("clicked", lambda x: self.stop_bot())
        self.create_bot_button.connect("clicked", lambda x: self.create_bot())

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.webview)

        url_box = Gtk.HBox()
        url_box.pack_start(self.get_bot_values_button, False, False, 0)
        url_box.pack_start(self.print_bot_values_button, False, False, 0)
        url_box.pack_start(self.run_bot_button, False, False, 0)
        url_box.pack_start(self.stop_bot_button, False, False, 0)
        url_box.pack_start(self.create_bot_button, False, False, 0)

        self.pack_start(url_box, False, False, 0)
        self.pack_start(scrolled_window, True, True, 0)

        url_box.show_all()
        scrolled_window.show_all()
        self.webview.load_uri("https://iss-sim.spacex.com/")

    def print_craft_values(self):
        print(f'rateRotationX (Pitch Speed): {self.rateRotationX[0]}')
        print(f'rateRotationY (Yaw Speed): {self.rateRotationY[0]}')
        print(f'rateRotationZ (Roll Speed): {self.rateRotationZ[0]}')
        print(f'fixedRotationX (Pitch): {self.fixedRotationX[0]}')
        print(f'fixedRotationY (Yaw):   {self.fixedRotationY[0]}')
        print(f'fixedRotationZ (Roll):   {self.fixedRotationZ[0]}')
        print(f'RateCurrent (Speed):   {self.rateCurrent[0]}')
        print(f'X (Position X):   {self.x[0]}')
        print(f'Y (Position X):   {self.y[0]}')
        print(f'Z (Position X):   {self.z[0]}')

    def create_bot(self):
        if self.bot is not None:
            self.bot.stop()
        self.bot = DumbBot(self)

    def start_bot(self):
        if self.bot is None:
            return
        self.bot.start()

    def stop_bot(self):
        if self.bot is None:
            return
        self.bot.stop()

    def get_fixed_rotation_x(self):
        return self.fixedRotationX[0]  # Pitch

    def get_fixed_rotation_y(self):
        return self.fixedRotationY[0]  # Yaw

    def get_fixed_rotation_z(self):
        return self.fixedRotationZ[0]  # Roll

    def get_rate_current(self):
        return self.rateCurrent[0]  # Velocity

    def get_rate_rotation_x(self):
        return self.rateRotationX[0]  # Pitch Speed

    def get_rate_rotation_y(self):
        return self.rateRotationY[0]  # Yaw Speed

    def get_rate_rotation_z(self):
        return self.rateRotationZ[0]  # Roll Speed

    def get_translation_x(self):
        return self.x[0]  # camera.position.z - issObject.position.z      # X

    def get_translation_z(self):
        return self.z[0]  # camera.position.y - issObject.position.y      # Z

    def get_translation_y(self):
        return self.y[0]  # camera.position.x - issObject.position.x      # Y

    def pitch_down(self):
        self.execute_javascript(self.pitchDown_javascript)

    def pitch_up(self):
        self.execute_javascript(self.pitchUp_javascript)

    def translate_up(self):
        self.execute_javascript(self.translateUp_javascript)

    def translate_down(self):
        self.execute_javascript(self.translateDown_javascript)

    def translate_backward(self):
        self.execute_javascript(self.translateBackward_javascript)

    def translate_forward(self):
        self.execute_javascript(self.translateForward_javascript)

    def translate_left(self):
        self.execute_javascript(self.translateLeft_javascript)

    def translate_right(self):
        self.execute_javascript(self.translateRight_javascript)

    def roll_left(self):
        self.execute_javascript(self.rollLeft_javascript)

    def roll_right(self):
        self.execute_javascript(self.rollRight_javascript)

    def yaw_left(self):
        self.execute_javascript(self.yawLeft_javascript)

    def yaw_right(self):
        self.execute_javascript(self.yawRight_javascript)

    def query_craft_values(self):

        # self.fixedRotationX = []     # Pitch
        self.webview.run_javascript("rateRotationX.toString()", None, self.set_double_callback, self.rateRotationX)
        # self.fixedRotationY = []     # Yaw
        self.webview.run_javascript("rateRotationY.toString()", None, self.set_double_callback, self.rateRotationY)
        # self.fixedRotationZ = []     # Roll
        self.webview.run_javascript("rateRotationZ.toString()", None, self.set_double_callback, self.rateRotationZ)
        self.webview.run_javascript("fixedRotationX.toString()", None, self.set_double_callback, self.fixedRotationX)
        self.webview.run_javascript("fixedRotationY.toString()", None, self.set_double_callback, self.fixedRotationY)
        self.webview.run_javascript("fixedRotationZ.toString()", None, self.set_double_callback, self.fixedRotationZ)
        # self.rateCurrent = []        # Velocity
        self.webview.run_javascript("rateCurrent.toString()", None, self.set_double_callback, self.rateCurrent)
        # self.y = []                  # camera.position.x - issObject.position.x      # Y
        self.webview.run_javascript("(camera.position.x - issObject.position.x).toString()", None,
                                    self.set_double_callback, self.y)
        # self.z = []                  # camera.position.y - issObject.position.y      # Z
        self.webview.run_javascript("(camera.position.y - issObject.position.y).toString()", None,
                                    self.set_double_callback, self.z)
        # self.x = []                  # camera.position.z - issObject.position.z      # X
        self.webview.run_javascript("(camera.position.z - issObject.position.z).toString()", None,
                                    self.set_double_callback, self.x)

    def set_double_callback(self, webview, result, user_data):
        """Callback to set the variable we just queried the value of"""
        js_result = self.webview.run_javascript_finish(result)
        user_data[0] = js_result.get_js_value().to_double()

    def execute_javascript(self, command):
        """Execute the javascript in our webview."""
        self.webview.run_javascript(command, None)


class Browser(Gtk.Window):
    """Part of original code lift,

    @@TODO: needs to be rewritten.

    Create browser tabs based on the known implementations available, currently it is only the iss-sim.

    """
    def __init__(self, *args, **kwargs):
        super(Browser, self).__init__(*args, **kwargs)

        # create notebook and tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)

        # basic stuff
        self.tabs = []
        self.set_size_request(1000, 1000)

        # create a first, empty browser tab
        self.tabs.append((ISSSimTab(), Gtk.Label("SpaceX ISS-SIM")))
        self.notebook.append_page(*self.tabs[0])
        self.add(self.notebook)

        # connect signals
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self._key_pressed)
        self.notebook.connect("switch-page", self._tab_changed)

        self.notebook.show()
        self.show()

    def _tab_changed(self, notebook, current_page, index):
        if not index:
            return
        title = self.tabs[index][0].webview.get_title()
        if title:
            self.set_title(title)

    def _title_changed(self, webview, frame, title):
        current_page = self.notebook.get_current_page()

        counter = 0
        for tab, label in self.tabs:
            if tab.webview is webview:
                label.set_text(title)
                if counter == current_page:
                    self._tab_changed(None, None, counter)
                break
            counter += 1

    def _create_tab(self):
        tab = ISSSimTab()
        return tab

    def _reload_tab(self):
        self.tabs[self.notebook.get_current_page()][0].webview.reload()

    def _close_current_tab(self):
        if self.notebook.get_n_pages() == 1:
            return
        page = self.notebook.get_current_page()
        current_tab = self.tabs.pop(page)
        self.notebook.remove(current_tab[0])

    def _open_new_tab(self):
        current_page = self.notebook.get_current_page()
        page_tuple = (self._create_tab(), Gtk.Label("New Tab"))
        self.tabs.insert(current_page + 1, page_tuple)
        self.notebook.insert_page(page_tuple[0], page_tuple[1], current_page + 1)
        self.notebook.set_current_page(current_page + 1)

    def _focus_url_bar(self):
        current_page = self.notebook.get_current_page()
        self.tabs[current_page][0].url_bar.grab_focus()

    def _raise_find_dialog(self):
        current_page = self.notebook.get_current_page()
        self.tabs[current_page][0].find_box.show_all()
        self.tabs[current_page][0].find_entry.grab_focus()

    def _key_pressed(self, widget, event):
        modifiers = Gtk.accelerator_get_default_mod_mask()
        mapping = {Gdk.KEY_r: self._reload_tab,
                   Gdk.KEY_w: self._close_current_tab,
                   Gdk.KEY_t: self._open_new_tab,
                   Gdk.KEY_l: self._focus_url_bar,
                   Gdk.KEY_f: self._raise_find_dialog,
                   Gdk.KEY_q: Gtk.main_quit}

        if event.state & modifiers == Gdk.ModifierType.CONTROL_MASK \
                and event.keyval in mapping:
            mapping[event.keyval]()


if __name__ == "__main__":
    Gtk.init(sys.argv)

    browser = Browser()

    Gtk.main()
