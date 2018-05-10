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

# Written by Benny Malengier
# Last change 2005/12/05:
# Correspond  naming of dates with actual action, so for abbreviation
# of month given by mnd. not MAAND
# Also less possibilities

"""
Dutch-specific classes for parsing and displaying dates.
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
# Dutch parser
#
#-------------------------------------------------------------------------
class DateParserNL(DateParser):

    month_to_int = DateParser.month_to_int
    # Always add dutch and flemish name variants
    # no matter what the current locale is
    month_to_int[u"januari"] = 1
    month_to_int[u"jan"]    = 1
    # Add other common latin, local and historical variants  
    month_to_int[u"januaris"] = 1
    month_to_int[u"feber"]  = 2
    month_to_int[u"februaris"]  = 2
    month_to_int[u"merz"]  = 3
    #make sure on all distro mrt and maa are accepted
    month_to_int[u"maa"]  = 3
    month_to_int[u"mrt"]  = 3
    month_to_int[u"aprilis"]  = 4
    month_to_int[u"maius"]  = 5
    month_to_int[u"junius"]  = 6
    month_to_int[u"julius"]  = 7
    month_to_int[u"augst"]  = 8
    month_to_int[u"7ber"]  = 9
    month_to_int[u"7bris"]  = 9
    month_to_int[u"8ber"]  = 10
    month_to_int[u"8bris"]  = 10
    month_to_int[u"9ber"]  = 11
    month_to_int[u"9bris"]  = 11
    month_to_int[u"10ber"]  = 12
    month_to_int[u"10bris"]  = 12
    month_to_int[u"xber"]  = 12
    month_to_int[u"xbris"]  = 12
    
    modifier_to_int = {
        u'voor'    : Date.MOD_BEFORE, 
        u'na'      : Date.MOD_AFTER, 
        u'tegen'   : Date.MOD_ABOUT, 
        u'om'      : Date.MOD_ABOUT, 
        u'rond'    : Date.MOD_ABOUT, 
        u'circa'   : Date.MOD_ABOUT, 
        u'ca.'     : Date.MOD_ABOUT, 
        }

    calendar_to_int = {
        u'gregoriaans'    : Date.CAL_GREGORIAN, 
        u'greg.'          : Date.CAL_GREGORIAN, 
        u'juliaans'       : Date.CAL_JULIAN, 
        u'jul.'           : Date.CAL_JULIAN, 
        u'hebreeuws'      : Date.CAL_HEBREW, 
        u'hebr.'          : Date.CAL_HEBREW, 
        u'islamitisch'      : Date.CAL_ISLAMIC, 
        u'isl.'           : Date.CAL_ISLAMIC, 
        u'franse republiek': Date.CAL_FRENCH, 
        u'fran.'         : Date.CAL_FRENCH, 
        u'persisch'       : Date.CAL_PERSIAN, 
        u'zweeds'          : Date.CAL_SWEDISH, 
        u'z'               : Date.CAL_SWEDISH, 
        }

    quality_to_int = {
        u'geschat' : Date.QUAL_ESTIMATED, 
        u'gesch.'    : Date.QUAL_ESTIMATED, 
        u'berekend' : Date.QUAL_CALCULATED, 
        u'ber.'      : Date.QUAL_CALCULATED, 
        }

    bce = ["voor onze tijdrekening", "voor Christus", "v. Chr."] + DateParser.bce
    
    def init_strings(self):
        DateParser.init_strings(self)
        self._span  = re.compile("(van)\s+(?P<start>.+)\s+(tot)\s+(?P<stop>.+)", 
                                 re.IGNORECASE)
        self._range  = re.compile("tussen\s+(?P<start>.+)\s+en\s+(?P<stop>.+)", 
                                  re.IGNORECASE)
        self._text2  = re.compile('(\d+)?.?\s+?%s\s*((\d+)(/\d+)?)?'
                                  % self._mon_str, 
                                  re.IGNORECASE)
        self._jtext2 = re.compile('(\d+)?.?\s+?%s\s*((\d+)(/\d+)?)?'
                                  % self._jmon_str, 
                                  re.IGNORECASE)

#-------------------------------------------------------------------------
#
# Dutch display
#
#-------------------------------------------------------------------------
class DateDisplayNL(DateDisplay):
    """
    Dutch language date display class. 
    """
    # TODO: Translate these month strings:
    long_months = ( u"", u"januari", u"februari", u"maart", u"april", u"mei", 
                    u"juni", u"juli", u"augustus", u"september", u"oktober", 
                    u"november", u"december" )
    
    short_months = ( u"", u"jan", u"feb", u"mrt", u"apr", u"mei", u"jun", 
                     u"jul", u"aug", u"sep", u"okt", u"nov", u"dec" )
    
    calendar = (
        "", u"juliaans", u"hebreeuws", 
        u"franse republiek", u"persisch", u"islamitisch",
        u"zweeds" )

    _mod_str = ("", u"voor ", u"na ", u"rond ", "", "", "")
    
    _qual_str = ("", u"geschat ", u"berekend ")
    
    _bce_str = "%s v. Chr."

    formats = (
        "JJJJ-MM-DD (ISO)", "Numerisch DD/MM/JJ", "Maand Dag, Jaar", 
        "Mnd. Dag Jaar", "Dag Maand Jaar", "Dag Mnd. Jaar"
        )
        # this definition must agree with its "_display_gregorian" method

    def _display_gregorian(self, date_val):
        """
        display gregorian calendar date in different format
        """
        # this must agree with its locale-specific "formats" definition
        year = self._slash_year(date_val[2], date_val[3])
        if self.format == 0:
            return self.display_iso(date_val)
        elif self.format == 1:
            if date_val[3]:
                return self.display_iso(date_val)
            else:
                # day/month_number/year
                if date_val[0] == date_val[1] == 0:
                    value = str(date_val[2])
                else:
                    value = self._tformat.replace('%m', str(date_val[1]))
                    value = value.replace('%d', str(date_val[0]))
                    value = value.replace('%Y', str(abs(date_val[2])))
                    value = value.replace('-', '/')
        elif self.format == 2:
            # month_name day, year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self.long_months[date_val[1]], year)
            else:
                value = "%s %d, %s" % (self.long_months[date_val[1]], 
                                       date_val[0], year)
        elif self.format == 3:
            # month_abbreviation day, year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self.short_months[date_val[1]], year)
            else:
                value = "%s %d, %s" % (self.short_months[date_val[1]], 
                                       date_val[0], year)
        elif self.format == 4:
            # day month_name year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self.long_months[date_val[1]], year)
            else:
                value = "%d %s %s" % (date_val[0], 
                                      self.long_months[date_val[1]], year)
        else:
            # day month_abbreviation year
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = "%s %s" % (self.short_months[date_val[1]], year)
            else:
                value = "%d %s %s" % (date_val[0], 
                                      self.short_months[date_val[1]], year)
        if date_val[2] < 0:
            return self._bce_str % value
        else:
            return value

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
            return ""
        elif mod == Date.MOD_SPAN:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return "%s%s %s %s %s%s" % (qual_str, u'van', d1, 
                                        u'tot', d2, scal)
        elif mod == Date.MOD_RANGE:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return "%stussen %s en %s%s" % (qual_str, d1, d2, 
                                            scal)
        else:
            text = self.display_cal[date.get_calendar()](start)
            scal = self.format_extras(cal, newyear)
            return "%s%s%s%s" % (qual_str, self._mod_str[mod], text, 
                                 scal)

#-------------------------------------------------------------------------
#
# Register classes
#
#-------------------------------------------------------------------------
register_datehandler(('nl_NL', 'dutch', 'Dutch', 'nl_BE', 'nl'), 
                     DateParserNL, DateDisplayNL)
