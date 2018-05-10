#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modiy
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

# Written by Alex Roitman

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
import time
from gen.ggettext import gettext as _
from itertools import chain

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gobject

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from QuestionDialog import QuestionDialog
import ManagedWindow

#-------------------------------------------------------------------------
#
# UndoHistory class
#
#-------------------------------------------------------------------------
class UndoHistory(ManagedWindow.ManagedWindow):
    """
    The UndoHistory provides a list view with all the editing
    steps available for undo/redo. Selecting a line in the list
    will revert/advance to the appropriate step in editing history.
    """
    
    def __init__(self, dbstate, uistate):

        self.title = _("Undo History")
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.db = dbstate.db
        self.undodb = self.db.undodb
        self.dbstate = dbstate

        window = gtk.Dialog("", uistate.window,
                            gtk.DIALOG_DESTROY_WITH_PARENT, None)

        self.undo_button = window.add_button(gtk.STOCK_UNDO,
                                             gtk.RESPONSE_REJECT)
        self.redo_button = window.add_button(gtk.STOCK_REDO,
                                             gtk.RESPONSE_ACCEPT)
        self.clear_button = window.add_button(gtk.STOCK_CLEAR,
                                              gtk.RESPONSE_APPLY)
        self.close_button = window.add_button(gtk.STOCK_CLOSE,
                                              gtk.RESPONSE_CLOSE)
     
        self.set_window(window, None, self.title)
        self.window.set_size_request(400, 200)
        self.window.connect('response', self._response)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.tree = gtk.TreeView()
        self.model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, 
                                   gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.selection = self.tree.get_selection()

        self.renderer = gtk.CellRendererText()
        self.tree.set_model(self.model)
        self.tree.set_rules_hint(True)
        self.tree.append_column(
            gtk.TreeViewColumn(_('Original time'), self.renderer,
                               text=0, foreground=2, background=3))
        self.tree.append_column(
            gtk.TreeViewColumn(_('Action'), self.renderer,
                               text=1, foreground=2, background=3))

        scrolled_window.add(self.tree)
        self.window.vbox.add(scrolled_window)
        self.window.show_all()

        self._build_model()
        self._update_ui()
        
        self.selection.connect('changed', self._selection_changed)
        self.show()

    def _selection_changed(self, obj):
        (model, node) = self.selection.get_selected()
        if not node:
            return
        path = self.model.get_path(node)
        start = min(path[0], self.undodb.undo_count)
        end = max(path[0], self.undodb.undo_count)

        self._paint_rows(0, len(self.model) - 1, False)
        self._paint_rows(start, end, True)

        if path[0] < self.undodb.undo_count:
            # This transaction is an undo candidate
            self.redo_button.set_sensitive(False)
            self.undo_button.set_sensitive(self.undodb.undo_count)

        else: # path[0] >= self.undodb.undo_count:
            # This transaction is an redo candidate
            self.undo_button.set_sensitive(False)
            self.redo_button.set_sensitive(self.undodb.redo_count)

    def _paint_rows(self, start, end, selected=False):
        if selected:
            (fg, bg) = get_colors(self.tree, gtk.STATE_SELECTED)
        else:
            fg = bg = None

        for idx in range(start, end+1):
            the_iter = self.model.get_iter( (idx,) )
            self.model.set(the_iter, 2, fg)
            self.model.set(the_iter, 3, bg)
            
    def _response(self, obj, response_id):
        if response_id == gtk.RESPONSE_CLOSE:
            self.close(obj)

        elif response_id == gtk.RESPONSE_REJECT:
            # Undo the selected entries
            (model, node) = self.selection.get_selected()
            if not node:
                return
            path = self.model.get_path(node)
            nsteps = path[0] - self.undodb.undo_count - 1
            self._move(nsteps or -1)

        elif response_id == gtk.RESPONSE_ACCEPT:
            # Redo the selected entries
            (model, node) = self.selection.get_selected()
            if not node:
                return
            path = self.model.get_path(node)
            nsteps = path[0] - self.undodb.undo_count
            self._move(nsteps or 1)

        elif response_id == gtk.RESPONSE_APPLY:
            self._clear_clicked()
        elif response_id == gtk.RESPONSE_DELETE_EVENT:
            self.close(obj)

    def build_menu_names(self, obj):
        return (self.title, None)

    def _clear_clicked(self, obj=None):
        QuestionDialog(_("Delete confirmation"),
                       _("Are you sure you want to clear the Undo history?"),
                       _("Clear"),
                       self.clear,
                       self.window)

    def clear(self):
        self.undodb.clear()
        self.db.abort_possible = False
        self.update()
        if self.db.undo_callback:
            self.db.undo_callback(None)
        if self.db.redo_callback:
            self.db.redo_callback(None)

    def _move(self, steps=-1):
        if steps == 0:
            return
        func = self.db.undo if steps < 0 else self.db.redo

        for step in range(abs(steps)):
            func(False)
        self.update()

    def _update_ui(self):
        self._paint_rows(0, len(self.model)-1, False)
        self.undo_button.set_sensitive(self.undodb.undo_count)
        self.redo_button.set_sensitive(self.undodb.redo_count)
        self.clear_button.set_sensitive(
            self.undodb.undo_count or self.undodb.redo_count
            )

    def _build_model(self):
        self.model.clear()
        fg = bg = None

        if self.undodb.undo_history_timestamp:
            if self.db.abort_possible:
                mod_text = _('Database opened')
            else:
                mod_text = _('History cleared')
            time_text = time.ctime(self.undodb.undo_history_timestamp)           
            self.model.append(row=[time_text, mod_text, fg, bg])

        # Add the undo and redo queues to the model
        for txn in chain(self.undodb.undoq, reversed(self.undodb.redoq)):
            time_text = time.ctime(txn.timestamp)
            mod_text = txn.get_description()
            self.model.append(row=[time_text, mod_text, fg, bg])
        path = (self.undodb.undo_count,)
        self.selection.select_path(path)

    def update(self):
        self._build_model()
        self._update_ui()

def gtk_color_to_str(color):
    color_str = u"#%02x%02x%02x" % (color.red/256,
                                    color.green/256,
                                    color.blue/256)
    return color_str

def get_colors(obj, state):
    fg_color = obj.style.fg[state]
    bg_color = obj.style.bg[state]

    fg_color_str = gtk_color_to_str(fg_color)
    bg_color_str = gtk_color_to_str(bg_color)

    return (fg_color_str, bg_color_str)
