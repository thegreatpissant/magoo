"""Magoo A bot to pilot the Spacex iss-sim webgl application at iss-sim.spacex.com

@author: James A. Feister
@email: openjaf@gmail.com

For now creates a webkit instance and a bot to pilot the iss craft ('webgl') camera within the iss-sim simulation.


I think the framework for the web application originated from https://gist.github.com/pydoh/2f1b8287276bb70d961e88842ebe741f

The intent is to generalize this automation to other webpages.
"""
import ast
import pathlib
import sys
import time
import threading

import gi
from enum import Enum

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.0")
from gi.repository import Gtk, GLib, Gdk, WebKit2


class DumbBot:
    """A very very dumb bot to pilot the craft.  Do not trust it."""

    def __init__(self, browser_window, bot_src="bots/dumb_bot.py"):
        self.run_bot = False
        self.thread_handle = None
        self.browser_window = browser_window
        self.bot_script = None
        self.bot_src = bot_src
        self.reset_src()

    def reset_src(self):
        with open(self.bot_src, "r") as bot_src:
            self.bot_script = str("".join(bot_src))

    def main_thread(self):
        if self.bot_script is None:
            return
        try:
            self.run_bot = True
            exec(self.bot_script)
        except Exception as e:
            print(f"Bot Script Error  {e}")
        print("main thread done")

    def thread_is_running(self):
        return self.thread_handle is not None and self.thread_handle.is_alive()

    def start(self):
        if self.thread_is_running():
            return
        self.thread_handle = threading.Thread(target=self.main_thread)
        self.thread_handle.daemon = True
        self.thread_handle.start()

    def stop(self):
        self.run_bot = False
        if self.thread_is_running():
            self.thread_handle.join(0.1)


class JavascriptType(Enum):
    """Enum values used to assign types."""

    DOUBLE = 1
    STRING = 2


class BrowserTab(Gtk.VBox):
    def __init__(self, *args, **kwargs):
        super(BrowserTab, self).__init__(*args, **kwargs)
        self.connect("destroy", self.on_destroy)

        #  This bots window
        self.webview = WebKit2.WebView()
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.webview)

        #  Buttons
        self.show_exposed_values_button = Gtk.Button.new_with_label("Exposed Values")
        self.show_exposed_values_button.connect("clicked", self.show_exposed_values)
        self.run_bot_button = Gtk.Button.new_with_label("Run Bot")
        self.run_bot_button.connect("clicked", self.start_bot)
        self.stop_bot_button = Gtk.Button.new_with_label("Stop Bot")
        self.stop_bot_button.connect("clicked", self.stop_bot)
        self.edit_bot_button = Gtk.Button.new_with_label("Edit Bot")
        self.edit_bot_button.connect("clicked", self.edit_bot)
        self.reload_bot_button = Gtk.Button.new_with_label("Reset Bot Script")
        self.reload_bot_button.connect("clicked", self.reset_bot_script)

        #  Button Container
        url_box = Gtk.HBox()
        url_box.pack_start(self.run_bot_button, False, False, 0)
        url_box.pack_start(self.stop_bot_button, False, False, 0)
        url_box.pack_start(self.edit_bot_button, False, False, 0)
        url_box.pack_start(self.reload_bot_button, False, False, 0)
        url_box.pack_start(self.show_exposed_values_button, False, False, 0)

        #  Add the container to this VBox
        self.pack_start(url_box, False, False, 0)
        self.pack_start(scrolled_window, True, True, 0)

        url_box.show_all()
        scrolled_window.show_all()
        self.show()

        self.webview.load_uri("https://iss-sim.spacex.com/")

        #  Declare the positions of these values.
        self.VARTYPE = 0
        self.VARJAVASCRIPT = 1
        self.VARVALUE = 2
        self.VARDESCRIPTION = 3
        self.CMDNAME = 0
        self.CMDJAVASCRIPT = 1

        #  Bots edit window
        self.edit_bot_window = None
        #  Bots Values Window
        self.values_window = None
        #  Bots AST Window
        self.ast_window = None
        #  Options for the interface
        # self.perform_periodic_bot_value_update = None
        # self.periodic_bot_value_update_time = 1

        #  The bot
        self.bot = None

        #  Setup Bot default bot
        self.bot = DumbBot(self)

        #  Declare this pages exposed information
        self.exposed_values = {
            "rateRotationX": [JavascriptType.DOUBLE, "rateRotationX", 0, "Pitch Speed"],
            "rateRotationY": [JavascriptType.DOUBLE, "rateRotationY", 0, "Yaw Speed"],
            "rateRotationZ": [JavascriptType.DOUBLE, "rateRotationZ", 0, "Roll Speed"],
            "fixedRotationX": [JavascriptType.DOUBLE, "fixedRotationX", 0, "Pitch"],
            "fixedRotationY": [JavascriptType.DOUBLE, "fixedRotationY", 0, "Yaw"],
            "fixedRotationZ": [JavascriptType.DOUBLE, "fixedRotationZ", 0, "Roll"],
            "rateCurrent": [JavascriptType.DOUBLE, "rateCurrent", 0, "Speed"],
            "positionY": [
                JavascriptType.DOUBLE,
                "camera.position.x - issObject.position.x",
                0,
                "Position X",
            ],
            "positionZ": [
                JavascriptType.DOUBLE,
                "camera.position.y - issObject.position.y",
                0,
                "Position Y",
            ],
            "positionX": [
                JavascriptType.DOUBLE,
                "camera.position.z - issObject.position.z",
                0,
                "Position Z",
            ],
        }
        #  Declare this pages exposed commands
        self.exposed_commands = {
            "rollLeft": "rollLeft()",
            "rollRight": "rollRight()",
            "pitchDown": "pitchDown()",
            "pitchUp": "pitchUp()",
            "yawLeft": "yawLeft()",
            "yawRight": "yawRight()",
            "translateForward": "translateForward()",
            "translateBackward": "translateBackward()",
            "translateDown": "translateDown()",
            "translateUp": "translateUp()",
            "translateRight": "translateRight()",
            "translateLeft": "translateLeft()",
        }
        self.exposed_values_update_thread_handle = threading.Thread(
            target=self.exposed_values_update_thread
        )
        self.exposed_values_update = True
        self.exposed_values_update_sleep_time = 0.3
        self.exposed_values_update_thread_handle.daemon = True
        self.exposed_values_update_thread_handle.start()

    def exposed_values_update_thread(self):
        """Thread that will periodically query the loaded page for the exposed values"""
        while self.exposed_values_update:
            GLib.idle_add(self.refresh_exposed_values)
            time.sleep(self.exposed_values_update_sleep_time)

    def execute_command(self, command):
        """Execute one of the available bot_commands as page javascript."""
        if command in self.exposed_commands:
            GLib.idle_add(self.execute_javascript, self.exposed_commands[command])
        else:
            print(f"User Command: {command} not available.")

    def show_exposed_values(self, button):
        """Create the page values window."""
        if self.values_window is not None:
            self.values_window.destroy()
        self.values_window = ValuesWindow(self)
        self.values_window.show()

    def get_exposed_value_display_buffer(self):
        """Retrieve a str of the exposed values"""
        buffer_text = ""
        for var in self.exposed_values:
            buffer_text += f"{var:20} ({self.exposed_values[var][self.VARDESCRIPTION]}): {self.exposed_values[var][self.VARVALUE]:5}\n"
        return buffer_text

    def start_bot(self, button):
        """Run the bot"""
        if self.bot is None:
            return
        self.stop_bot()
        self.update_bot_string_contents()
        self.bot.start()

    def stop_bot(self, button=None):
        """Stop the bot"""
        if self.bot is None:
            return
        self.bot.stop()

    def edit_bot(self, button):
        """Create the edit bot window."""
        if self.edit_bot_window is not None:
            self.edit_bot_window.destroy()
        self.edit_bot_window = EditBotWindow(self)
        self.edit_bot_window.show()
        self.ast_window = ASTWindow(self)
        self.ast_window.show()

    def reset_bot_script(self, button):
        """Reload the bot script from its default"""
        self.bot.reset_src()
        self.edit_bot_window.load_bot_script()

    def update_bot_string_contents(self):
        """Query the edit window for the updated bot contents
        and set the running bot script to those contents."""
        if self.edit_bot_window is not None:
            self.bot.bot_script = self.edit_bot_window.get_bot_script()

    def get_value(self, value_string):
        """Retrieve one of the exposed values."""
        if value_string in self.exposed_values:
            return self.exposed_values[value_string][self.VARVALUE]
        return f"{value_string} is an unknown variable"

    def get_value_callback(self, javascript_type):
        """Callback that will assign the queried value to the exposed value storage object."""
        if javascript_type == JavascriptType.DOUBLE:
            return self.set_double_callback
        if javascript_type == JavascriptType.STRING:
            return self.set_string_callback

    def refresh_exposed_values(self):
        """Refresh all the exposed values values from the page"""
        for var in self.exposed_values:
            self.webview.run_javascript(
                f"({self.exposed_values[var][self.VARJAVASCRIPT]}).toString()",
                None,
                self.get_value_callback(self.exposed_values[var][self.VARTYPE]),
                var,
            )

    def set_string_callback(self, webiew, result, user_data):
        """Callback to set the variable we just queried the value of as a string type."""
        try:
            js_result = self.webview.run_javascript_finish(result)
            value = js_result.get_js_value().to_string()
        except GLib.GError as ge:
            value = "<unknown>"
        self.exposed_values[user_data][self.VARVALUE] = value

    def set_double_callback(self, webview, result, user_data):
        """Callback to set the variable we just queried the value of as a double type"""
        try:
            js_result = self.webview.run_javascript_finish(result)
            value = js_result.get_js_value().to_double()
        except GLib.GError as ge:
            value = "<unknown>"
        self.exposed_values[user_data][self.VARVALUE] = value

    def execute_javascript(self, command):
        """Execute the javascript in our webview."""
        self.webview.run_javascript(command, None)

    def on_destroy(self, event):
        self.exposed_values_update = False
        if self.bot is not None:
            self.bot.stop()
        if self.edit_bot_window is not None:
            self.edit_bot_window.destroy()
        if self.values_window is not None:
            self.values_window.destroy()


class EditBotWindow(Gtk.Window):
    """Window to edit the bot script"""

    def __init__(self, main_window):
        super(EditBotWindow, self).__init__()
        self.connect("destroy", self.on_destroy)

        self.set_default_size(800, 850)
        self.main_window = main_window
        self.bot = main_window.bot
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_border_width(5)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.buffer = Gtk.TextBuffer()
        self.connect("key-press-event", self.on_keypress)
        self.connect("key-release-event", self.on_keyrelease)
        self.text_view = Gtk.TextView(buffer=self.buffer)
        scrolled_window.add(self.text_view)
        self.add(scrolled_window)
        self.set_title("Edit Bot")
        self.show_all()
        self.load_bot_script()
        self.control_event = False

    def load_bot_script(self):
        self.set_bot_script(self.bot.bot_script)

    def set_bot_script(self, bot_text):
        self.buffer.set_text(bot_text)

    def get_bot_script(self):
        startIter, endIter = self.buffer.get_bounds()
        return self.buffer.get_text(startIter, endIter, False)

    def on_destroy(self, event):
        self.bot.bot_script = self.get_bot_script()

    def on_keypress(self, widget, event):
        print("Keypress")
        if event.keyval == Gdk.KEY_Control_R:
            self.control_event = True
            print("CTRL")
        if self.control_event and event.keyval == Gdk.KEY_Return:
            print("Enter")
            print("Got the CTRL-Enter")
            self.main_window.ast_window.load_bot_ast(self.get_bot_script())

    def on_keyrelease(self, widget, event):
        print("KeyRelease")
        if event.keyval == Gdk.KEY_Control_R:
            print("Ctrl")
            self.control_event = False

class ASTWindow(Gtk.Window):
    """Show the current AST
    """
    def __init__(self, main_window):
        super(ASTWindow, self).__init__()
        
        self.set_default_size(800, 850)
        self.main_window = main_window
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_border_width(5)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.buffer = Gtk.TextBuffer()
        self.text_view = Gtk.TextView(buffer=self.buffer)
        scrolled_window.add(self.text_view)
        self.add(scrolled_window)
        self.set_title("AST Window")
        self.show_all()
    
    def load_bot_ast(self, bot_script):
        ast_parse = ast.parse(bot_script)
        self.buffer.set_text(ast.dump(ast_parse, indent=4))


class ValuesWindow(Gtk.Window):
    """Window to show the bot values"""

    def __init__(self, bot_window):
        super(ValuesWindow, self).__init__()
        self.bot_window = bot_window
        # self.set_border_width(5)
        # self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.buffer = Gtk.TextBuffer()
        self.text_view = Gtk.TextView(buffer=self.buffer)
        self.text_view.set_cursor_visible(False)
        self.add(self.text_view)
        self.set_title("Exposed Values")
        self.show_all()

        self.thread_handle = threading.Thread(target=self.main_thread)
        self.thread_handle.daemon = True
        self.perform_periodic_value_update = True
        self.periodic_value_update_sleep_time = 1.0
        self.thread_handle.start()

    def set_display(self, values):
        """Update the text display with these values"""
        self.buffer.set_text(values)

    def main_thread(self):
        """Run the main query thread to request an updated display text"""
        while self.perform_periodic_value_update:
            GLib.idle_add(self.periodic_value_update)
            time.sleep(self.periodic_value_update_sleep_time)

    def periodic_value_update(self):
        """Update our display text with the current exposed values"""
        self.set_display(self.bot_window.get_exposed_value_display_buffer())


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
        self.tabs.append((BrowserTab(), Gtk.Label(label="SpaceX ISS-SIM")))
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
        tab = BrowserTab()
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
        mapping = {
            Gdk.KEY_r: self._reload_tab,
            Gdk.KEY_w: self._close_current_tab,
            Gdk.KEY_t: self._open_new_tab,
            Gdk.KEY_l: self._focus_url_bar,
            Gdk.KEY_f: self._raise_find_dialog,
            Gdk.KEY_q: Gtk.main_quit,
        }

        if (
            event.state & modifiers == Gdk.ModifierType.CONTROL_MASK
            and event.keyval in mapping
        ):
            mapping[event.keyval]()


if __name__ == "__main__":
    Gtk.init(sys.argv)

    browser = Browser()

    Gtk.main()
