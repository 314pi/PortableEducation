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
# Python modules
#
#-------------------------------------------------------------------------
import locale
import os

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".DateHandler")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from _DateParser import DateParser
from _DateDisplay import DateDisplay, DateDisplayEn
import constfunc

#-------------------------------------------------------------------------
#
# Constants 
#
#-------------------------------------------------------------------------
if not constfunc.win():
    LANG = locale.getlocale(locale.LC_TIME)[0]
else:
 if 'LC_TIME' in os.environ:
     LANG = os.environ['LC_TIME']
 elif 'LANG' in os.environ:
     LANG = os.environ['LANG']
 else:
     LANG = locale.getdefaultlocale(locale.LC_TIME)[0]

# If LANG contains ".UTF-8" use only the part to the left of "."
# Otherwise some date handler will not load. 
if LANG and ".UTF-8" in LANG.upper():
    LANG = LANG.split(".")[0]
    
if not LANG:
    if "LANG" in os.environ:
        LANG = os.environ["LANG"]

if LANG:
    LANG_SHORT = LANG.split('_')[0]
else:
    LANG_SHORT = "C"

LANG_TO_PARSER = {
    'C'                     : DateParser,
    'en'                    : DateParser,
    'English_United States' : DateParser,
    }

LANG_TO_DISPLAY = {
    'C'                     : DateDisplayEn,
    'en'                    : DateDisplayEn,
    'English_United States' : DateDisplayEn,
    'zh_CN'                 : DateDisplay,
    'zh_TW'                 : DateDisplay,
    'zh_SG'                 : DateDisplay,
    'zh_HK'                 : DateDisplay,
    'ja_JP'                 : DateDisplay,
    'ko_KR'                 : DateDisplay,
    'nb_NO'                 : DateDisplay,
    }

def register_datehandler(locales,parse_class,display_class):
    """
    Registers the passed date parser class and date displayer
    classes with the specified language locales.

    @param locales: tuple of strings containing language codes.
        The character encoding is not included, so the language
        should be in the form of fr_FR, not fr_FR.utf8
    @type locales: tuple
    @param parse_class: Class to be associated with parsing
    @type parse_class: DateParse
    @param display_class: Class to be associated with displaying
    @type display_class: DateDisplay
    """
    for lang_str in locales:
        LANG_TO_PARSER[lang_str] = parse_class
        LANG_TO_DISPLAY[lang_str] = display_class
