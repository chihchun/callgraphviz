#!/usr/bin/env python
#
# Copyright 2008 Jose Fonseca
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os

import gtk
import gtk.gdk

# On debian, xdot isn't installed in the system namespace:
sys.path.insert(1, '/usr/share/xdot')
import xdot
import gobject
import gtk
import gtk.gdk


class MyDotWindow(xdot.DotWindow):

    ui = '''
    <ui>
        <toolbar name="ToolBar">
            <toolitem action="Open"/>
            <separator/>
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
        </toolbar>
    </ui>
    '''


    def __init__(self):
        xdot.DotWindow.__init__(self)
        self.widget.connect('clicked', self.on_url_clicked)
        toolbar = self.uimanager.get_widget('/ToolBar')
        vbox = self.get_child()

        hbox = gtk.HBox()

        label = gtk.Label("Search symbols: ");
        hbox.pack_start(label, False)
        label.show()

        entry = gtk.Entry(max=0)
        hbox.pack_start(entry, True, True, 10)
        entry.show()

        vbox.pack_start(hbox, False)
        vbox.reorder_child(hbox, 1)
        hbox.show()

    def on_url_clicked(self, widget, url, event):
        dialog = gtk.MessageDialog(
                parent = self, 
                buttons = gtk.BUTTONS_OK,
                message_format="%s clicked" % url)
        dialog.connect('response', lambda dialog, response: dialog.destroy())
        dialog.run()
        return True

    def set_dotcode(self, dotcode, filename='<stdin>'):
        if self.widget.set_dotcode(dotcode, filename):
            self.set_title(os.path.basename(filename) + ' - Code Visualizer')
            self.widget.zoom_to_fit()

    def set_xdotcode(self, xdotcode, filename='<stdin>'):
        if self.widget.set_xdotcode(xdotcode):
            self.set_title(os.path.basename(filename) + ' - Code Visualizer')
            self.widget.zoom_to_fit()


dotcode = """
digraph G {
  Hello [UR2="http://en.wikipedia.org/wiki/Hello"]
  World [URL="http://en.wikipedia.org/wiki/World"]
    Hello -> World
}
"""


def main():
    window = MyDotWindow()
    window.set_dotcode(dotcode)
    window.set_dotcode(dotcode)
    window.connect('destroy', gtk.main_quit)
    gtk.main()


if __name__ == '__main__':
    main()
