#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
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
Secondary Object class for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.baseobj import BaseObject

#-------------------------------------------------------------------------
#
# Secondary Object class
#
#-------------------------------------------------------------------------
class SecondaryObject(BaseObject):
    """
    The SecondaryObject is the base class for all secondary objects in the
    database. 
    """
    
    def is_equal(self, source):
        return cmp(self.serialize(), source.serialize()) == 0

    def is_equivalent(self, other):
        """
        Return if this object is equivalent to other.

        Should be overwritten by objects that inherit from this class.
        """
        pass
