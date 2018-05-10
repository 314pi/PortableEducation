#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010    Nick Hall
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
Tag object for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gen.lib.tableobj import TableObject

#-------------------------------------------------------------------------
#
# Tag class
#
#-------------------------------------------------------------------------
class Tag(TableObject):
    """
    The Tag record is used to store information about a tag that can be
    attached to a primary object.
    """

    def __init__(self, source=None):
        """
        Create a new Tag instance, copying from the source if present.

        :param source: A tag used to initialize the new tag
        :type source: Tag
        """

        TableObject.__init__(self, source)
        
        if source:
            self.__name = source.__name
            self.__color = source.__color
            self.__priority = source.__priority
        else:
            self.__name = ""
            self.__color = "#000000000000" # Black
            self.__priority = 0

    def serialize(self):
        """
        Convert the data held in the event to a Python tuple that
        represents all the data elements. 
        
        This method is used to convert the object into a form that can easily 
        be saved to a database.

        These elements may be primitive Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objects or
        lists), the database is responsible for converting the data into
        a form that it can use.

        :returns: Returns a python tuple containing the data that should
            be considered persistent.
        :rtype: tuple
        """
        return (self.handle,
                self.__name,
                self.__color,
                self.__priority,
                self.change)

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in a Tag structure.

        :param data: tuple containing the persistent data associated the
            Person object
        :type data: tuple
        """
        (self.handle,
         self.__name,
         self.__color,
         self.__priority,
         self.change) = data

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.__name]

    def is_empty(self):
        """
        Return True if the Tag is an empty object (no values set).

        :returns: True if the Tag is empty
        :rtype: bool
        """
        return self.__name != ""

    def are_equal(self, other):
        """
        Return True if the passed Tag is equivalent to the current Tag.

        :param other: Tag to compare against
        :type other: Tag
        :returns: True if the Tags are equal
        :rtype: bool
        """
        if other is None:
            other = Tag()

        if self.__name != other.__name or \
           self.__color != other.__color or \
           self.__priority != other.__priority:
            return False
        return True

    def set_name(self, name):
        """
        Set the name of the Tag to the passed string.

        :param the_type: Name to assign to the Tag
        :type the_type: str
        """
        self.__name = name

    def get_name(self):
        """
        Return the name of the Tag.

        :returns: Name of the Tag
        :rtype: str
        """
        return self.__name
    name = property(get_name, set_name, None,
                    'Returns or sets name of the tag')

    def set_color(self, color):
        """
        Set the color of the Tag to the passed string. 
        
        The string is of the format #rrrrggggbbbb.

        :param color: Color to assign to the Tag
        :type color: str
        """
        self.__color = color

    def get_color(self) :
        """
        Return the color of the Tag.

        :returns: Returns the color of the Tag
        :rtype: str
        """
        return self.__color
    color = property(get_color, set_color, None,
                     'Returns or sets color of the tag')

    def set_priority(self, priority):
        """
        Set the priority of the Tag to the passed integer. 
        
        The lower the value the higher the priority.

        :param priority: Priority to assign to the Tag
        :type priority: int
        """
        self.__priority = priority

    def get_priority(self) :
        """
        Return the priority of the Tag.

        :returns: Returns the priority of the Tag
        :rtype: int
        """
        return self.__priority
    priority = property(get_priority, set_priority, None,
                     'Returns or sets priority of the tag')

