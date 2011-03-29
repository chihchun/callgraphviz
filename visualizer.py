#!/usr/bin/env python
#
# Copyright 2010 Rex Tsai <chihchun@kalug.linux.org.tw>
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
import subprocess

import gobject
import gtk
import gtk.gdk

# On debian, xdot isn't installed in the system namespace:
sys.path.insert(1, '/usr/share/xdot')
import xdot

class Visualizer(xdot.DotWindow):

    interest = {}
    working_dir = None
    filename = None

    def __init__(self):
        xdot.DotWindow.__init__(self)
        self.widget.connect('clicked', self.on_url_clicked)

        toolbar = self.uimanager.get_widget('/ToolBar')

        item = gtk.ToolButton(gtk.STOCK_SAVE)
        item.set_tooltip_markup("Save")
        item.connect('clicked', self.on_save)
        item.show()
        toolbar.insert(item, 0)

        item = gtk.ToolButton(gtk.STOCK_NEW)
        item.set_tooltip_markup("New project")
        item.connect('clicked', self.on_newproject)
        item.show()
        toolbar.insert(item, 0)
        
        vbox = self.get_child()
        hbox = gtk.HBox()

        label = gtk.Label("Search symbol: ");
        hbox.pack_start(label, False)
        label.show()

        entry = gtk.Entry(max=0)
        entry.connect('activate', self.on_symbol_enter)
        hbox.pack_start(entry, True, True, 10)
        entry.show()

        vbox.pack_start(hbox, False)
        vbox.reorder_child(hbox, 1)
        hbox.show()

        """ code brower, maybe someday I will implement it """
#        text = gtk.TextBuffer()
#        text.set_text("Hello world")
#        viewer = gtk.TextView(text)
#        vbox.pack_start(viewer, False)
#        viewer.show()

    def on_symbol_enter(self, widget):
        symbol = widget.get_text()
        widget.set_text('')
        if self.working_dir is None:
            # FIXME: let's have a dialog for the user.
            self.on_newproject(None)
        self.addSymbol(symbol)

    def addSymbol(self, symbol, lazy=0):
        # TODO: sould Saving the filename and line number.
        if(symbol == '//'):
            return

        if(lazy == 0):
            defs, calls = self.functionDefincation(symbol)
            if len(defs) >= 1:
                self.interest[symbol] = 1
            self.update_graph()
        else:
            self.interest[symbol] = 1
        pass

    def update_graph(self):
        """ update dot code based on the interested keys """
        funcs = set(self.interest.keys())
        if len(funcs) <= 0:
            self.widget.graph = xdot.Graph()
            return

        dotcode = "digraph G {"
        for func in funcs:
            dotcode += "\"%s\";" % func
            allFuncs, funsCalled = self.functionsCalled (func)
            for m in (allFuncs & funcs):
                dotcode += "\"%s\" -> \"%s\";" % (func, m)
        dotcode += "}"
        self.set_dotcode(dotcode)

        # saving the data.
        if self.filename is not None:
            fileObj = open(self.filename,"w") 
            fileObj.write("// %s\n" % self.working_dir)
            fileObj.write("// %s\n" % ' '.join(funcs))
            fileObj.write(dotcode)
            fileObj.close()

    def on_url_clicked(self, widget, url, event):
        dialog = gtk.MessageDialog(parent = self, buttons = gtk.BUTTONS_OK, message_format="%s clicked" % url)
        dialog.connect('response', lambda dialog, response: dialog.destroy())
        dialog.run()
        return True

    def set_dotcode(self, dotcode, filename=''):
        if self.widget.set_dotcode(dotcode, filename):
            self.set_title(os.path.basename(filename) + ' - Code Visualizer')
            self.widget.zoom_to_fit()

    def set_xdotcode(self, xdotcode, filename=''):
        if self.widget.set_xdotcode(xdotcode):
            self.set_title(os.path.basename(filename) + ' - Code Visualizer')
            self.widget.zoom_to_fit()

    def cscope(self, mode, func):
        # TODO: check the cscope database is exist.
        cmd = "cscope -d -l -L -%d %s" % (mode, func) 
        process = subprocess.Popen(cmd, stdout = subprocess.PIPE, shell = True, cwd = self.working_dir) 
        csoutput = process.stdout.read() 
        del process
        cslines = [arr.strip().split(' ') for arr in csoutput.split('\n') if len(arr.split(' '))>1] 
        allFuns = set(map(lambda x:x[1], cslines))

        funsCalled = {}
        for fl in cslines:
            if funsCalled.has_key(fl[0]):
                funsCalled[fl[0]] |= set([fl[1]])
            else:
                funsCalled[fl[0]] = set([fl[1]])

        return (allFuns, funsCalled)

    def functionDefincation(self, func):
        return self.cscope(1, func)

    def functionsCalled(self, func):
        # Find functions called by this function:
        return self.cscope(2, func)

    def functionsCalling(self, func):
        # Find functions calling this function:
        return self.cscope(3, func)

    def update_database(self):
        if not os.path.isfile(self.working_dir + "/cscope.out"):
            dialog = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
            dialog.set_default_response(gtk.RESPONSE_YES)
            dialog.set_markup("Create cscope database for %s now ?" % self.working_dir )
            ret = dialog.run()
            dialog.destroy()
            if ret == gtk.RESPONSE_YES:
                cmd = "cscope -bkRu"
                process = subprocess.call(cmd, shell = True, cwd = self.working_dir) 
                del process
        pass


    def on_open(self, action):
        chooser = gtk.FileChooserDialog(title="Open dot File",
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)) 
        chooser.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("Graphviz dot files")
        filter.add_pattern("*.dot")
        chooser.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            chooser.destroy()
            self.open_file(filename)
        else:
            chooser.destroy()

    def on_save(self, action):
        chooser = gtk.FileChooserDialog(title="Save your work",
                                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("Graphviz dot files")
        filter.add_pattern("*.dot")
        chooser.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        if chooser.run() == gtk.RESPONSE_OK:
            self.filename = chooser.get_filename()
            self.update_graph()
        chooser.destroy()
        pass

    def on_newproject(self, action):
        chooser = gtk.FileChooserDialog(title="Open the source code directory",
                                        action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        if chooser.run() == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            self.working_dir = filename
            self.interest = {}
            self.filename = None
            self.update_database()
            self.update_graph()

        chooser.destroy()
        pass

    def open_file(self, filename):
        try:
            fp = file(filename, 'rt')
            cfgs = [arr.strip().split(' ') for arr in fp.read().split('\n') if len(arr.split(' '))>1] 
            if cfgs[0][0] == '//':
                self.working_dir = cfgs[0][1]
            if cfgs[1][0] == '//':
                for i in cfgs[1]:
                    self.addSymbol(i, True)
            fp.close()
            self.update_graph()
            self.filename = filename
        except IOError, ex:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                    message_format=str(ex),
                                    buttons=gtk.BUTTONS_OK)
            dlg.run()
            dlg.destroy()

def main():
    window = Visualizer()
    window.connect('destroy', gtk.main_quit)
    gtk.main()

if __name__ == '__main__':
    main()
