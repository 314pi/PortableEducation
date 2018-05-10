#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
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
Repository Reference class for GRAMPS
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.secondaryobj import SecondaryObject
from gen.lib.privacybase import PrivacyBase
from gen.lib.notebase import NoteBase
from gen.lib.refbase import RefBase
from gen.lib.srcmediatype import SourceMediaType
from gen.lib.const import IDENTICAL, EQUAL, DIFFERENT

#-------------------------------------------------------------------------
#
# Repository Reference for Sources
#
#-------------------------------------------------------------------------
class RepoRef(SecondaryObject, PrivacyBase, NoteBase, RefBase):
    """
    Repository reference class.
    """

    def __init__(self, source=None):
        PrivacyBase.__init__(self, source)
        NoteBase.__init__(self, source)
        RefBase.__init__(self, source)
        if source:
            self.call_number = source.call_number
            self.media_type = SourceMediaType(source.media_type)
        else:
            self.call_number = ""
            self.media_type = SourceMediaType()

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return (
            NoteBase.serialize(self),
            RefBase.serialize(self),
            self.call_number, self.media_type.serialize(),
            PrivacyBase.serialize(self),
            )

    def unserialize(self, data):
        """
        Convert a serialized tuple of data to an object.
        """
        (note_list, ref, self.call_number, media_type, privacy) = data
        self.media_type = SourceMediaType()
        self.media_type.unserialize(media_type)
        PrivacyBase.unserialize(self, privacy)
        NoteBase.unserialize(self, note_list)
        RefBase.unserialize(self, ref)
        return self

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.call_number, str(self.media_type)]

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        ret = self.get_referenced_note_handles()
        if self.ref:
            ret += [('Repository', self.ref)]
        return ret

    def is_equivalent(self, other):
        """
        Return if this repository reference is equivalent, that is agrees in
        reference, call number and medium, to other.

        :param other: The repository reference to compare this one to.
        :rtype other: RepoRef
        :returns: Constant indicating degree of equivalence.
        :rtype: int
        """
        if self.ref != other.ref or \
            self.get_text_data_list() != other.get_text_data_list():
            return DIFFERENT
        else:
            if self.is_equal(other):
                return IDENTICAL
            else:
                return EQUAL

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this repository reference.

        :param acquisition: The repository reference to merge with the present
            repository reference.
        :rtype acquisition: RepoRef
        """
        self._merge_privacy(acquisition)
        self._merge_note_list(acquisition)

    def set_call_number(self, number):
        self.call_number = number

    def get_call_number(self):
        return self.call_number

    def get_media_type(self):
        return self.media_type

    def set_media_type(self, media_type):
        self.media_type.set(media_type)
