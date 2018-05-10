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

"""
The TreeModel for the Address list in the Address Tab.
"""

#-------------------------------------------------------------------------
#
# GTK libraries
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import DateHandler

#-------------------------------------------------------------------------
#
# AddressModel
#
#-------------------------------------------------------------------------
class AddressModel(gtk.ListStore):
    """
    AddressModel derives from the ListStore, defining te items in the list
    """

    def __init__(self, obj_list, dbase):
        """
        AddressModel derives from the ListStore, defining te items in the list
        """
        gtk.ListStore.__init__(self, str, str, str, str, str, str, object)
        self.db = dbase
        for obj in obj_list:
            self.append(row=[
                DateHandler.get_date(obj), 
                obj.street, 
                obj.locality, 
                obj.city, 
                obj.state, 
                obj.country, 
                obj, 
                ])
