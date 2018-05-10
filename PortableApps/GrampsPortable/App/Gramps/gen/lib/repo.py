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
Repository object for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.primaryobj import PrimaryObject
from gen.lib.notebase import NoteBase
from gen.lib.addressbase import AddressBase
from gen.lib.urlbase import UrlBase
from gen.lib.repotype import RepositoryType
from gen.lib.citationbase import IndirectCitationBase

#-------------------------------------------------------------------------
#
# Repository class
#
#-------------------------------------------------------------------------
class Repository(NoteBase, AddressBase, UrlBase, IndirectCitationBase,
        PrimaryObject):
    """A location where collections of Sources are found."""
    
    def __init__(self):
        """
        Create a new Repository instance.
        """
        PrimaryObject.__init__(self)
        NoteBase.__init__(self)
        AddressBase.__init__(self)
        UrlBase.__init__(self)
        self.type = RepositoryType()
        self.name = ""

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return (self.handle, self.gramps_id, self.type.serialize(),
                unicode(self.name),
                NoteBase.serialize(self),
                AddressBase.serialize(self),
                UrlBase.serialize(self),
                self.change, self.private)

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in a Repository structure.
        """
        (self.handle, self.gramps_id, the_type, self.name, note_list,
         address_list, urls, self.change, self.private) = data

        self.type = RepositoryType()
        self.type.unserialize(the_type)
        NoteBase.unserialize(self, note_list)
        AddressBase.unserialize(self, address_list)
        UrlBase.unserialize(self, urls)
        return self
        
    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.name, str(self.type)]

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return self.address_list + self.urls

    def get_citation_child_list(self):
        """
        Return the list of child secondary objects that may refer citations.

        :returns: Returns the list of child secondary child objects that may 
                refer citations.
        :rtype: list
        """
        return self.address_list

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may 
                refer notes.
        :rtype: list
        """
        return self.address_list

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        return self.get_citation_child_list()

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        return self.get_referenced_note_handles()

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this repository.

        :param acquisition: The repository to merge with the present repository.
        :rtype acquisition: Repository
        """
        self._merge_privacy(acquisition)
        self._merge_address_list(acquisition)
        self._merge_url_list(acquisition)
        self._merge_note_list(acquisition)

    def set_type(self, the_type):
        """
        :param the_type: descriptive type of the Repository
        :type the_type: str
        """
        self.type.set(the_type)

    def get_type(self):
        """
        :returns: the descriptive type of the Repository
        :rtype: str
        """
        return self.type

    def set_name(self, name):
        """
        :param name: descriptive name of the Repository
        :type name: str
        """
        self.name = name

    def get_name(self):
        """
        :returns: the descriptive name of the Repository
        :rtype: str
        """
        return self.name
