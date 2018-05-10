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
import gtk
import gobject

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import gen.lib
import Errors
from DdTargets import DdTargets
from webmodel import WebModel
from embeddedlist import EmbeddedList

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------
class WebEmbedList(EmbeddedList):

    _HANDLE_COL = 3
    _DND_TYPE   = DdTargets.URL

    _MSG = {
        'add'   : _('Create and add a new web address'),
        'del'   : _('Remove the existing web address'),
        'edit'  : _('Edit the selected web address'),
        'up'    : _('Move the selected web address upwards'),
        'down'  : _('Move the selected web address downwards'),
        'jump'  : _('Jump to the selected web address'),
    }

    #index = column in model. Value =
    #  (name, sortcol in model, width, markup/text, weigth_col
    _column_names = [
        (_('Type')       , 0, 100, 0, -1), 
        (_('Path')       , 1, 200, 0, -1), 
        (_('Description'), 2, 150, 0, -1), 
        ]
    
    def __init__(self, dbstate, uistate, track, data):
        self.data = data
        EmbeddedList.__init__(self, dbstate, uistate, track, _('_Internet'), 
                              WebModel, move_buttons=True, jump_button=True)

    def get_icon_name(self):
        return 'gramps-url'

    def get_data(self):
        return self.data

    def column_order(self):
        return ((1, 0), (1, 1), (1, 2))

    def add_button_clicked(self, obj):
        from gui.editors import EditUrl
        url = gen.lib.Url()
        try:
            EditUrl(self.dbstate, self.uistate, self.track, 
                    '', url, self.add_callback)
        except Errors.WindowActiveError:
            pass

    def add_callback(self, url):
        data = self.get_data()
        data.append(url)
        self.rebuild()
        gobject.idle_add(self.tree.scroll_to_cell, len(data) - 1)

    def edit_button_clicked(self, obj):
        from gui.editors import EditUrl
        url = self.get_selected()
        if url:
            try:
                EditUrl(self.dbstate, self.uistate, self.track, 
                        '', url, self.edit_callback)
            except Errors.WindowActiveError:
                pass

    def edit_callback(self, url):
        self.rebuild()

    def get_popup_menu_items(self):
        return [ 
            (True,  True,  gtk.STOCK_ADD,     self.add_button_clicked),
            (False, True,  gtk.STOCK_EDIT,    self.edit_button_clicked),
            (True,  True,  gtk.STOCK_REMOVE,  self.del_button_clicked),
            (True,  True,  gtk.STOCK_JUMP_TO, self.jump_button_clicked),
            ]

    def jump_button_clicked(self, obj):
        import GrampsDisplay

        url = self.get_selected()
        if url.get_path():
            GrampsDisplay.url(url.get_path())
