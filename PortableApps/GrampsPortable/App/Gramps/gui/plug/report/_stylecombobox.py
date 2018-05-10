#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2010       Jakim Friant
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

from gen.ggettext import gettext as _

import gtk
import gobject

#-------------------------------------------------------------------------
#
# StyleComboBox
#
#-------------------------------------------------------------------------
class StyleComboBox(gtk.ComboBox):
    """
    Derived from the ComboBox, this widget provides handling of Report
    Styles.
    """

    def __init__(self,model=None):
        """
        Initialize the combobox, building the display column.
        """
        gtk.ComboBox.__init__(self,model)
        cell = gtk.CellRendererText()
        self.pack_start(cell,True)
        self.add_attribute(cell,'text',0)
        
    def set(self,style_map,default):
        """
        Set the options for the ComboBox, using the passed style
        map as the data.

        @param style_map: dictionary of style names and the corresponding
            style sheet
        @type style_map: dictionary
        @param default: Default selection in the ComboBox
        @type default: str
        """
        self.store = gtk.ListStore(gobject.TYPE_STRING)
        self.set_model(self.store)
        self.style_map = style_map
        start_index = 0
        for index, key in enumerate(sorted(style_map)):
            if key == "default":
                self.store.append(row=[_('default')])
            else:
                self.store.append(row=[key])
            if key == default:
                start_index = index
            
        self.set_active(start_index)

    def get_value(self):
        """
        Return the selected key (style sheet name).

        @returns: Returns the name of the selected style sheet
        @rtype: str
        """
        active = self.get_active()
        if active < 0:
            return None
        key = unicode(self.store[active][0])
        if key == _('default'):
            key = "default"
        return (key,self.style_map[key])
