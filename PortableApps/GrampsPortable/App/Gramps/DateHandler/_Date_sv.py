# -*- coding: utf-8 -*-
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
Swedish-specific classes for parsing and displaying dates.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import re

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib import Date
from _DateParser import DateParser
from _DateDisplay import DateDisplay
from _DateHandler import register_datehandler

#-------------------------------------------------------------------------
#
# Swedish parser class
#
#-------------------------------------------------------------------------
class DateParserSv(DateParser):
    """
    Convert a text string into a Date object, expecting a date
    notation in the swedish language. If the date cannot be converted, 
    the text string is assigned.
    """

    # modifiers before the date
    modifier_to_int = {
        u'före'    : Date.MOD_BEFORE, 
        u'innan'   : Date.MOD_BEFORE, 
        u'efter'   : Date.MOD_AFTER, 
        u'omkring' : Date.MOD_ABOUT, 
        u'ca'      : Date.MOD_ABOUT, 
        u'c:a'     : Date.MOD_ABOUT
        }

    bce = [u"f Kr"]

    calendar_to_int = {
        u'gregoriansk   '      : Date.CAL_GREGORIAN, 
        u'g'                   : Date.CAL_GREGORIAN, 
        u'juliansk'            : Date.CAL_JULIAN, 
        u'j'                   : Date.CAL_JULIAN, 
        u'hebreisk'            : Date.CAL_HEBREW, 
        u'h'                   : Date.CAL_HEBREW, 
        u'islamisk'            : Date.CAL_ISLAMIC, 
        u'muslimsk'            : Date.CAL_ISLAMIC, 
        u'i'                   : Date.CAL_ISLAMIC, 
        u'fransk'              : Date.CAL_FRENCH, 
        u'fransk republikansk' : Date.CAL_FRENCH, 
        u'f'                   : Date.CAL_FRENCH, 
        u'persisk'             : Date.CAL_PERSIAN, 
        u'p'                   : Date.CAL_PERSIAN, 
        u'svensk'              : Date.CAL_SWEDISH, 
        u's'                   : Date.CAL_SWEDISH, 
        }
    
    quality_to_int = {
        u'uppskattat' : Date.QUAL_ESTIMATED, 
        u'uppskattad' : Date.QUAL_ESTIMATED, 
        u'bedömt'     : Date.QUAL_ESTIMATED, 
        u'bedömd'     : Date.QUAL_ESTIMATED, 
        u'beräknat'   : Date.QUAL_CALCULATED, 
        u'beräknad'   : Date.QUAL_CALCULATED, 
        }
    
    def init_strings(self):
        """ Define, in Swedish, span and range regular expressions"""
        DateParser.init_strings(self)
        self._span     = re.compile(u"(från)?\s*(?P<start>.+)\s*(till|--|–)\s*(?P<stop>.+)", 
                                    re.IGNORECASE)
        self._range    = re.compile(u"(mellan)\s+(?P<start>.+)\s+och\s+(?P<stop>.+)", 
                                    re.IGNORECASE)

#-------------------------------------------------------------------------
#
# Swedish display class
#
#-------------------------------------------------------------------------
class DateDisplaySv(DateDisplay):
    """
    Swedish language date display class. 
    """
    long_months = ( u"", u"januari", u"februari", u"mars", u"april", u"maj", 
                    u"juni", u"juli", u"augusti", u"september", u"oktober", 
                    u"november", u"december" )
    
    short_months = ( u"", u"jan", u"feb", u"mar", u"apr", u"maj", u"jun",
                      u"jul", u"aug", u"sep", u"okt", u"nov", u"dec" )
    
    formats = (
        u"ÅÅÅÅ-MM-DD (ISO)", 
        u"År/mån/dag", 
        u"Månad dag, år", 
        u"MÅN DAG ÅR", 
        u"Dag månad år", 
        u"DAG MÅN ÅR", 
        )
        # this must agree with DateDisplayEn's "formats" definition
        # (since no locale-specific _display_gregorian exists, here)

    calendar = (
        u"", 
        u"juliansk", 
        u"hebreisk", 
        u"fransk republikansk", 
        u"persisk", 
        u"islamisk", 
        u"svensk"
        )
    
    _mod_str = (u"", u"före ", u"efter ", u"c:a ", u"", u"", u"")

    _qual_str = (u"", u"uppskattat ", u"beräknat ")
    
    _bce_str = u"%s f Kr"

    def display(self, date):
        """
        Return a text string representing the date.
        """
        mod = date.get_modifier()
        cal = date.get_calendar()
        qual = date.get_quality()
        start = date.get_start_date()
        newyear = date.get_new_year()

        qual_str = self._qual_str[qual]

        if mod == Date.MOD_TEXTONLY:
            return date.get_text()
        elif start == Date.EMPTY:
            return u""
        elif mod == Date.MOD_SPAN:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return u"%sfrån %s till %s%s" % (qual_str, d1, d2, scal)
        elif mod == Date.MOD_RANGE:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return u"%smellan %s och %s%s" % (qual_str, d1, d2, 
                                              scal)
        else:
            text = self.display_cal[date.get_calendar()](start)
            scal = self.format_extras(cal, newyear)
            return u"%s%s%s%s" % (qual_str, self._mod_str[mod], 
                                 text, scal)

#-------------------------------------------------------------------------
#
# Register classes
#
#-------------------------------------------------------------------------
register_datehandler(('sv_SE', 'sv_SE.UTF-8', 'sv', 'Swedish'), DateParserSv, DateDisplaySv)
