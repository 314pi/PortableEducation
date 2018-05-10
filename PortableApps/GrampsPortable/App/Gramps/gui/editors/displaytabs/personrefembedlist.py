#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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
from gen.ggettext import gettext as _
import gobject

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import gen.lib
import Errors
from DdTargets import DdTargets
from personrefmodel import PersonRefModel
from embeddedlist import EmbeddedList

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class PersonRefEmbedList(EmbeddedList):

    _HANDLE_COL = 3
    _DND_TYPE   = DdTargets.PERSONREF

    _MSG = {
        'add'   : _('Create and add a new association'),
        'del'   : _('Remove the existing association'),
        'edit'  : _('Edit the selected association'),
        'up'    : _('Move the selected association upwards'),
        'down'  : _('Move the selected association downwards'),
    }

    #index = column in model. Value =
    #  (name, sortcol in model, width, markup/text
    _column_names = [
        (_('Name'), 0, 250, 0, -1), 
        (_('ID'), 1, 100, 0, -1), 
        (_('Association'), 2, 100, 0, -1), 
        ]
    
    def __init__(self, dbstate, uistate, track, data):
        self.data = data
        EmbeddedList.__init__(self, dbstate, uistate, track, 
                              _('_Associations'), PersonRefModel, 
                              move_buttons=True)

    def get_ref_editor(self):
        from gui.editors import EditPersonRef
        return EditPersonRef

    def get_data(self):
        return self.data

    def column_order(self):
        return ((1, 0), (1, 1), (1, 2))

    def add_button_clicked(self, obj):
        from gui.editors import EditPersonRef
        try:
            ref = gen.lib.PersonRef()
            ref.rel = _('Godfather')
            EditPersonRef(
                self.dbstate, self.uistate, self.track,
                ref, self.add_callback)
        except Errors.WindowActiveError:
            pass

    def add_callback(self, obj):
        data = self.get_data()
        data.append(obj)
        self.rebuild()
        gobject.idle_add(self.tree.scroll_to_cell, len(data) - 1)

    def edit_button_clicked(self, obj):
        from gui.editors import EditPersonRef
        ref = self.get_selected()
        if ref:
            try:
                EditPersonRef(
                    self.dbstate, self.uistate, self.track,
                    ref, self.edit_callback)
            except Errors.WindowActiveError:
                pass

    def edit_callback(self, obj):
        self.rebuild()

    def _handle_drag(self, row, obj):
        """
        And event reference that is from a drag and drop has
        an unknown event reference type
        """
        from gui.editors import EditPersonRef
        try:
            ref = gen.lib.PersonRef(obj)
            ref.rel = _('Unknown')
            EditPersonRef(
                self.dbstate, self.uistate, self.track,
                ref, self.add_callback)
        except Errors.WindowActiveError:
            pass
