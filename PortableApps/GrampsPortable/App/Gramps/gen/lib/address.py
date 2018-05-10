#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
# Copyright (C) 2011       Tim G L Lyons
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
Address class for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.secondaryobj import SecondaryObject
from gen.lib.privacybase import PrivacyBase
from gen.lib.citationbase import CitationBase
from gen.lib.notebase import NoteBase
from gen.lib.datebase import DateBase
from gen.lib.locationbase import LocationBase
from gen.lib.const import IDENTICAL, EQUAL, DIFFERENT

#-------------------------------------------------------------------------
#
# Address for Person/Repository
#
#-------------------------------------------------------------------------
class Address(SecondaryObject, PrivacyBase, CitationBase, NoteBase, DateBase,
              LocationBase):
    """Provide address information."""

    def __init__(self, source=None):
        """
        Create a new Address instance, copying from the source if provided.
        """
        PrivacyBase.__init__(self, source)
        CitationBase.__init__(self, source)
        NoteBase.__init__(self, source)
        DateBase.__init__(self, source)
        LocationBase.__init__(self, source)

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return (PrivacyBase.serialize(self),
                CitationBase.serialize(self),
                NoteBase.serialize(self),
                DateBase.serialize(self),
                LocationBase.serialize(self))

    def unserialize(self, data):
        """
        Convert a serialized tuple of data to an object.
        """
        (privacy, citation_list, note_list, date, location) = data
        
        PrivacyBase.unserialize(self, privacy)
        CitationBase.unserialize(self, citation_list)
        NoteBase.unserialize(self, note_list)
        DateBase.unserialize(self, date)
        LocationBase.unserialize(self, location)
        return self

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return LocationBase.get_text_data_list(self)

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return []

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may refer notes.
        :rtype: list
        """
        return []

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        return []

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        return self.get_referenced_note_handles() + \
                self.get_referenced_citation_handles()

    def is_equivalent(self, other):
        """
        Return if this address is equivalent, that is agrees in location and
        date, to other.

        :param other: The address to compare this one to.
        :rtype other: Address
        :returns: Constant indicating degree of equivalence.
        :rtype: int
        """
        if self.get_text_data_list() != other.get_text_data_list() or \
            self.get_date_object() != other.get_date_object():
            return DIFFERENT
        else:
            if self.is_equal(other):
                return IDENTICAL
            else:
                return EQUAL

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this address.

        Lost: date, street, city, county, state, country, postal and phone of
        acquisition. 

        :param acquisition: The address to merge with the present address.
        :rtype acquisition: Address
        """
        self._merge_privacy(acquisition)
        self._merge_note_list(acquisition)
        self._merge_citation_list(acquisition)
