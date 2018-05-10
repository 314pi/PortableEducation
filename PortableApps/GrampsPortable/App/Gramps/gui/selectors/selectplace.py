#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2006  Donald N. Allingham
# Copyright (C) 2009-2010  Gary Burton
# Copyright (C) 2010       Nick Hall
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
# internationalization
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gui.views.treemodels.placemodel import PlaceListModel
from baseselector import BaseSelector

#-------------------------------------------------------------------------
#
# SelectPlace
#
#-------------------------------------------------------------------------
class SelectPlace(BaseSelector):

    def _local_init(self):
        """
        Perform local initialisation for this class
        """
        self.width_key = 'interface.place-sel-width'
        self.height_key = 'interface.place-sel-height'

    def get_window_title(self):
        return _("Select Place")
        
    def get_model_class(self):
        return PlaceListModel

    def get_column_titles(self):
        return [
            (_('Title'),   350, BaseSelector.TEXT, 0),
            (_('ID'),       75, BaseSelector.TEXT, 1),
            (_('Street'),   75, BaseSelector.TEXT, 2),
            (_('Locality'), 75, BaseSelector.TEXT, 3),
            (_('City'),     75, BaseSelector.TEXT, 4),
            (_('County'),   75, BaseSelector.TEXT, 5),
            (_('State'),    75, BaseSelector.TEXT, 6),
            (_('Country'),  75, BaseSelector.TEXT, 7),
            (_('Parish'),   75, BaseSelector.TEXT, 9),
            (_('Last Change'), 150, BaseSelector.TEXT, 12),
            ]

    def get_from_handle_func(self):
        return self.db.get_place_from_handle
        
    def get_handle_column(self):
        return PlaceListModel.HANDLE_COL
