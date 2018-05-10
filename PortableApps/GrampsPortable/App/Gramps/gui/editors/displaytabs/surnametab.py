#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2010       Benny Malengier
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

#-------------------------------------------------------------------------
#
# Python classes
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _
import locale

#-------------------------------------------------------------------------
#
# GTK classes
#
#-------------------------------------------------------------------------
import gtk
import gobject
import pango
_TAB = gtk.gdk.keyval_from_name("Tab")
_ENTER = gtk.gdk.keyval_from_name("Enter")

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
from surnamemodel import SurnameModel
from embeddedlist import EmbeddedList
from DdTargets import DdTargets
import AutoComp
from gen.lib import Surname, NameOriginType

#-------------------------------------------------------------------------
#
# SurnameTab
#
#-------------------------------------------------------------------------
class SurnameTab(EmbeddedList):

    _HANDLE_COL = 5
    _DND_TYPE   = DdTargets.SURNAME
    
    _MSG = {
        'add'   : _('Create and add a new surname'),
        'del'   : _('Remove the selected surname'),
        'edit'  : _('Edit the selected surname'),
        'up'    : _('Move the selected surname upwards'),
        'down'  : _('Move the selected surname downwards'),
    }
    
    #index = column in model. Value =
    #  (name, sortcol in model, width, markup/text
    _column_names = [
        (_('Prefix'), -1, 150, 0, -1),
        (_('Surname'), -1, 250, 0, -1),
        (_('Connector'), -1, 100, 0, -1),
        ]
    _column_combo = (_('Origin'), -1, 150, 3)  # name, sort, width, modelcol
    _column_toggle = (_('Name|Primary'), -1, 80, 4)
    
    def __init__(self, dbstate, uistate, track, name, on_change=None,
                 top_label=_('<b>Multiple Surnames</b>')):
        self.obj = name
        self.on_change = on_change
        self.curr_col = -1
        self.curr_cellr = None
        self.curr_celle = None
        
        EmbeddedList.__init__(self, dbstate, uistate, track, _('Family Surnames'), 
                              SurnameModel, move_buttons=True, 
                              top_label=top_label)

    def build_columns(self):
        #first the standard text columns with normal method
        EmbeddedList.build_columns(self)

        # Need to add attributes to renderers
        # and connect renderers to the 'edited' signal
        for colno in range(len(self.columns)):
            for renderer in self.columns[colno].get_cell_renderers():
                renderer.set_property('editable', not self.dbstate.db.readonly)
                renderer.connect('editing_started', self.on_edit_start, colno)
                renderer.connect('edited', self.on_edit_inline, self.column_order()[colno][1])
        
        # now we add the two special columns
        # combobox for type
        colno = len(self.columns)
        name = self._column_combo[0]
        renderer = gtk.CellRendererCombo()
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        # set up the comboentry editable
        no = NameOriginType()
        self.cmborig = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        self.cmborigmap = no.get_map().copy()
        keys = sorted(self.cmborigmap, self.by_value)
        for key in keys:
            if key != no.get_custom():
                self.cmborig.append(row=[key, self.cmborigmap[key]])
        additional = self.dbstate.db.get_origin_types()
        if additional:
            for type in additional:
                if type:
                    self.cmborig.append(row=[no.get_custom(), type])
        renderer.set_property("model", self.cmborig)
        renderer.set_property("text-column", 1)
        renderer.set_property('editable', not self.dbstate.db.readonly)

        renderer.connect('editing_started', self.on_edit_start_cmb, colno)
        renderer.connect('edited', self.on_orig_edited, self._column_combo[3])
        # add to treeview
        column = gtk.TreeViewColumn(name, renderer, text=self._column_combo[3])
        column.set_resizable(True)
        column.set_sort_column_id(self._column_combo[1])
        column.set_min_width(self._column_combo[2])
        column.set_expand(True)
        self.columns.append(column)
        self.tree.append_column(column)
        # toggle box for primary
        colno += 1
        name = self._column_toggle[0]
        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.set_property('radio', True)
        renderer.connect( 'toggled', self.on_prim_toggled, self._column_toggle[3])
        # add to treeview
        column = gtk.TreeViewColumn(name, renderer, active=self._column_toggle[3])
        column.set_resizable(False)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_alignment(0.5)
        column.set_sort_column_id(self._column_toggle[1])
        column.set_min_width(self._column_toggle[2])
        self.columns.append(column)
        self.tree.append_column(column)

    def by_value(self, first, second):
        """
        Method for sorting keys based on the values.
        """
        fvalue = self.cmborigmap[first]
        svalue = self.cmborigmap[second]
        return locale.strcoll(fvalue, svalue)

    def get_data(self):
        return self.obj.get_surname_list()

    def is_empty(self):
        return len(self.model)==0

    def _get_surn_from_model(self):
        """
        Return new surname_list for storing in the name based on content of
        the model
        """
        new_list = []
        for idx in range(len(self.model)):
            node = self.model.get_iter(idx)
            surn = self.model.get_value(node, 5)
            surn.set_prefix(unicode(self.model.get_value(node, 0)))
            surn.set_surname(unicode(self.model.get_value(node, 1)))
            surn.set_connector(unicode(self.model.get_value(node, 2)))
            surn.get_origintype().set(unicode(self.model.get_value(node, 3)))
            surn.set_primary(self.model.get_value(node, 4))
            new_list += [surn]
        return new_list
        
    def update(self):
        """
        Store the present data in the model to the name object
        """
        new_map = self._get_surn_from_model()
        self.obj.set_surname_list(new_map)
        # update name in previews
        if self.on_change:
            self.on_change()

    def column_order(self):
        # order of columns for EmbeddedList. Only the text columns here
        return ((1, 0), (1, 1), (1, 2))

    def add_button_clicked(self, obj):
        """Add button is clicked, add a surname to the person"""
        prim = False
        if len(self.obj.get_surname_list()) == 0:
            prim = True
        node = self.model.append(row=['', '', '', NameOriginType(), prim, 
                                      Surname()])
        self.selection.select_iter(node)
        path = self.model.get_path(node)
        self.tree.set_cursor_on_cell(path,
                                     focus_column=self.columns[0],
                                     focus_cell=None,
                                     start_editing=True)
        self.update()

    def del_button_clicked(self, obj):
        """
        Delete button is clicked. Remove from the model
        """
        (model, node) = self.selection.get_selected()
        if node:
            self.model.remove(node)
            self.update()

    def on_edit_start(self, cellr, celle, path, colnr):
        """ start of editing. Store stuff so we know when editing ends where we
        are
        """
        self.curr_col = colnr
        self.curr_cellr = cellr
        self.curr_celle = celle
    
    def on_edit_start_cmb(self, cellr, celle, path, colnr):
        """
        An edit starts in the origin type column
        This means a cmb has been created as celle, and we can set up the stuff
        we want this cmb to contain: autocompletion, stop edit when selection
        in the cmb happens.
        """
        self.on_edit_start(cellr, celle, path, colnr)
        #set up autocomplete
        completion = gtk.EntryCompletion()
        completion.set_model(self.cmborig)
        completion.set_minimum_key_length(1)
        completion.set_text_column(1)
        celle.child.set_completion(completion)
        #
        celle.connect('changed', self.on_origcmb_change, path, colnr)

    def on_edit_start_toggle(self, cellr, celle, path, colnr):
        """
        Edit
        """
        self.on_edit_start(cellr, celle, path, colnr)

    def on_edit_inline(self, cell, path, new_text, colnr):
        """
        Edit is happening. The model is updated and the surname objects updated.
        colnr must be the column in the model.
        """
        node = self.model.get_iter(path)
        self.model.set_value(node, colnr, new_text)
        self.update()

    def on_orig_edited(self, cellr, path, new_text, colnr):
        """
        An edit is finished in the origin type column. For a cmb in an editor,
        the model may only be updated when typing is finished, as editing stops
        automatically on update of the model.
        colnr must be the column in the model.
        """
        self.on_edit_inline(cellr, path, new_text, colnr)

    def on_origcmb_change(self, cmb, path, colnr):
        """
        A selection occured in the cmb of the origin type column. colnr must
        be the column in the model.
        """
        act = cmb.get_active()
        if act == -1:
            return
        self.on_orig_edited(None, path, 
                            self.cmborig.get_value(
                                            self.cmborig.get_iter((act,)),1),
                            colnr)

    def on_prim_toggled(self, cell, path, colnr):
        """
        Primary surname on path is toggled. colnr must be the col 
        in the model
        """
        #obtain current value
        node = self.model.get_iter(path)
        old_val = self.model.get_value(node, colnr)
        for nr in range(len(self.obj.get_surname_list())):
            if nr == int(path[0]):
                if old_val:
                    #True remains True
                    break
                else:
                    #This value becomes True
                    self.model.set_value(self.model.get_iter((nr,)), colnr, True)
            else:
                self.model.set_value(self.model.get_iter((nr,)), colnr, False)
        self.update()
        return

    def edit_button_clicked(self, obj):
        """ Edit button clicked
        """
        (model, node) = self.selection.get_selected()
        if node:
            path = self.model.get_path(node)
            self.tree.set_cursor_on_cell(path,
                                         focus_column=self.columns[0],
                                         focus_cell=None,
                                         start_editing=True)

    def key_pressed(self, obj, event):
        """
        Handles the key being pressed. 
        Here we make sure tab moves to next or previous value in row on TAB
        """
        if not EmbeddedList.key_pressed(self, obj, event):
            if event.type == gtk.gdk.KEY_PRESS and event.keyval in (_TAB,):
                if not (event.state & (gtk.gdk.SHIFT_MASK |
                                       gtk.gdk.CONTROL_MASK)):
                    return self.next_cell()
                elif (event.state & (gtk.gdk.SHIFT_MASK |
                                     gtk.gdk.CONTROL_MASK)):
                    return self.prev_cell()
                else:
                    return
            else:
                return
        return True

    def next_cell(self):
        """
        Move to the next cell to edit it
        """           
        (model, node) = self.selection.get_selected()
        if node:
            path = int(self.model.get_path(node)[0])
            nccol = self.curr_col+1
            if  nccol < 4:
                self.tree.set_cursor_on_cell(path,
                                         focus_column=self.columns[nccol],
                                         focus_cell=None,
                                         start_editing=True)
            elif nccol == 4:
                #go to next line if there is one
                if path < len(self.obj.get_surname_list()):
                    newpath = (path+1,)
                    self.selection.select_path(newpath)
                    self.tree.set_cursor_on_cell(newpath,
                                     focus_column=self.columns[0],
                                     focus_cell=None,
                                     start_editing=True)
                else:
                    #stop editing
                    self.curr_celle.editing_done()
                    return
        return True
                    
        
    def prev_cell(self):
        """
        Move to the next cell to edit it
        """     
        (model, node) = self.selection.get_selected()
        if node:
            path = int(self.model.get_path(node)[0])
            if  self.curr_col > 0:
                self.tree.set_cursor_on_cell(path,
                                         focus_column=self.columns[self.curr_col-1],
                                         focus_cell=None,
                                         start_editing=True)
            elif self.curr_col == 0:
                #go to prev line if there is one
                if path > 0:
                    newpath = (path-1,)
                    self.selection.select_path(newpath)
                    self.tree.set_cursor_on_cell(newpath,
                                     focus_column=self.columns[-2],
                                     focus_cell=None,
                                     start_editing=True)
                else:
                    #stop editing
                    self.curr_celle.editing_done()
                    return
        return True
