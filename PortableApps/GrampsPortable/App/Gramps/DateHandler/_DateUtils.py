#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2006  Donald N. Allingham
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
Class handling language-specific selection for date parser and displayer.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from DateHandler import LANG_TO_DISPLAY, LANG, parser, displayer

#--------------------------------------------------------------
#
# Convenience functions
#
#--------------------------------------------------------------
def get_date_formats():
    """
    Return the list of supported formats for date parsers and displayers.
    """
    try:
        return LANG_TO_DISPLAY[LANG].formats
    except:
        return LANG_TO_DISPLAY["C"].formats

def set_format(value):
    try:
        displayer.set_format(value)
    except:
        pass

def set_date(date_base, text) :
    """
    Set the date of the DateBase instance.
    
    The date is parsed into a Date instance.
    
    @param date_base: The DateBase instance to set the date to.
    @type date_base: DateBase
    @param text: The text to use for the text string in date
    @type text: str
    
    """
    parser.set_date(date_base.get_date_object(), text)

def get_date(date_base) :
    """
    Return a string representation of the date of the DateBase instance.
    
    This representation is based off the default date display format
    determined by the locale's DateDisplay instance.
    @return: Returns a string representing the DateBase date
    @rtype: str
    
    """
    return displayer.display(date_base.get_date_object())

def get_date_valid(date_base):
    date_obj = date_base.get_date_object()
    return date_obj.get_valid()
