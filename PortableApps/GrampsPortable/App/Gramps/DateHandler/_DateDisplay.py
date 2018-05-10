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
U.S English date display class. Should serve as the base class for all
localized tasks.
"""

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".DateDisplay")

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib import Date
import GrampsLocale

#-------------------------------------------------------------------------
#
# DateDisplay
#
#-------------------------------------------------------------------------
class DateDisplay(object):
    """
    Base date display class. 
    """
    long_months = ( u"", u"January", u"February", u"March", u"April", u"May", 
                    u"June", u"July", u"August", u"September", u"October", 
                    u"November", u"December" )
    
    short_months = ( u"", u"Jan", u"Feb", u"Mar", u"Apr", u"May", u"Jun",
                     u"Jul", u"Aug", u"Sep", u"Oct", u"Nov", u"Dec" )

    _tformat = GrampsLocale.tformat

    hebrew = (
        "", "Tishri", "Heshvan", "Kislev", "Tevet", "Shevat", 
        "AdarI", "AdarII", "Nisan", "Iyyar", "Sivan", "Tammuz", 
        "Av", "Elul"
        )
    
    french = (
        u'', 
        u"Vendémiaire", 
        u'Brumaire', 
        u'Frimaire', 
        u"Nivôse", 
        u"Pluviôse", 
        u"Ventôse", 
        u'Germinal', 
        u"Floréal", 
        u'Prairial', 
        u'Messidor', 
        u'Thermidor', 
        u'Fructidor', 
        u'Extra', 
        )
    
    persian = (
        "", "Farvardin", "Ordibehesht", "Khordad", "Tir", 
        "Mordad", "Shahrivar", "Mehr", "Aban", "Azar", 
        "Dey", "Bahman", "Esfand"
        )
    
    islamic = (
        "", "Muharram", "Safar", "Rabi`al-Awwal", "Rabi`ath-Thani", 
        "Jumada l-Ula", "Jumada t-Tania", "Rajab", "Sha`ban", 
        "Ramadan", "Shawwal", "Dhu l-Qa`da", "Dhu l-Hijja"
        )

    swedish = (
        "", "Januari", "Februari", "Mars",
        "April", "Maj", "Juni",
        "Juli", "Augusti", "September",
        "Oktober", "November", "December"
        )

    formats = ("YYYY-MM-DD (ISO)", )
    # this will be overridden if a locale-specific date displayer exists

    calendar = (
        "", "Julian", "Hebrew", "French Republican", 
        "Persian", "Islamic", "Swedish" 
        )
    # this will be overridden if a locale-specific date displayer exists

    newyear = ("", "Mar1", "Mar25", "Sep1")
    
    _mod_str = ("", "before ", "after ", "about ", "", "", "")
    # this will be overridden if a locale-specific date displayer exists

    _qual_str = ("", "estimated ", "calculated ")
    # this will be overridden if a locale-specific date displayer exists
    
    _bce_str = "%s B.C.E."
    # this will be overridden if a locale-specific date displayer exists

    def __init__(self, format=None):
        self.display_cal = [
            self._display_gregorian, 
            self._display_julian, 
            self._display_hebrew, 
            self._display_french, 
            self._display_persian, 
            self._display_islamic, 
            self._display_swedish]

        if format is None:
            self.format = 0
        else:
            self.format = format

    def set_format(self, format):
        self.format = format

    def format_extras(self, cal, newyear):
        """
        Formats the extra items (calendar, newyear) for a date.
        """
        scal = self.calendar[cal]
        if isinstance(newyear, int) and newyear <= len(self.newyear):
            snewyear = self.newyear[newyear]
        elif isinstance(newyear, (list, tuple)):
            snewyear = "%s-%s" % (newyear[0], newyear[1])
        else:
            snewyear = "Err"
        retval = ""
        for item in [scal, snewyear]:
            if item:
                if retval:
                    retval += ", "
                retval += item
        if retval:
            return " (%s)" % retval
        return ""

    def display(self, date):
        """
        Return a text string representing the date.
        (will be overridden if a locale-specific date displayer exists)
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
        elif mod == Date.MOD_SPAN or mod == Date.MOD_RANGE:
            d1 = self.display_iso(start)
            d2 = self.display_iso(date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return "%s %s - %s%s" % (qual_str, d1, d2, scal)
        else:
            text = self.display_iso(start)
            scal = self.format_extras(cal, newyear)
            return "%s%s%s%s" % (qual_str, self._mod_str[mod], text, scal)

    def _slash_year(self, val, slash):
        if val < 0:
            val = - val
            
        if slash:
            if (val-1) % 100 == 99:
                year = "%d/%d" % (val - 1, (val%1000))
            elif (val-1) % 10 == 9:
                year = "%d/%d" % (val - 1, (val%100))
            else:
                year = "%d/%d" % (val - 1, (val%10))
        else:
            year = "%d" % (val)
        
        return year
        
    def display_iso(self, date_val):
        # YYYY-MM-DD (ISO)
        year = self._slash_year(date_val[2], date_val[3])
        # This produces 1789, 1789-00-11 and 1789-11-00 for incomplete dates.
        if date_val[0] == date_val[1] == 0:
            # No month and no day -> year
            value = year
        else:
            value = "%s-%02d-%02d" % (year, date_val[1], date_val[0])
        if date_val[2] < 0:
            return self._bce_str % value
        else:
            return value

    def _display_gregorian(self, date_val):
        # this one must agree with DateDisplayEn's "formats" definition
        # (it may be overridden if a locale-specific date displayer exists)
        year = self._slash_year(date_val[2], date_val[3])
        if self.format == 0:
            return self.display_iso(date_val)
        elif self.format == 1:
            # numerical
            if date_val[3]:
                return self.display_iso(date_val)
            else:
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
        # elif self.format == 5:
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

    def _display_julian(self, date_val):
        # Julian date display is the same as Gregorian
        return self._display_gregorian(date_val)

    def _display_calendar(self, date_val, month_list):
        # used to display non-Gregorian calendars (Hebrew, Islamic, etc.)
        year = abs(date_val[2])
        if self.format == 0 or self.format == 1:
            return self.display_iso(date_val)
        else:
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = u"%s %d" % (month_list[date_val[1]], year)
            else:
                value = u"%s %d, %s" % (month_list[date_val[1]], date_val[0], 
                                        year)
        if date_val[2] < 0:
            return self._bce_str % value
        else:
            return value

    def _display_french(self, date_val):
        year = abs(date_val[2])
        if self.format == 0 or self.format == 1:
            return self.display_iso(date_val)
        else:
            if date_val[0] == 0:
                if date_val[1] == 0:
                    value = year
                else:
                    value = u"%s %d" % (self.french[date_val[1]], year)
            else:
                value = u"%d %s %s" % (date_val[0], self.french[date_val[1]], 
                                       year)
        if date_val[2] < 0:
            return self._bce_str % value
        else:
            return value

    def _display_hebrew(self, date_val):
        return self._display_calendar(date_val, self.hebrew)

    def _display_persian(self, date_val):
        return self._display_calendar(date_val, self.persian)

    def _display_islamic(self, date_val):
        return self._display_calendar(date_val, self.islamic)

    def _display_swedish(self, date_val):
        return self._display_calendar(date_val, self.swedish)

class DateDisplayEn(DateDisplay):
    """
    English language date display class. 
    """

    formats = (
        "YYYY-MM-DD (ISO)", "Numerical", "Month Day, Year", 
        "MON DAY, YEAR", "Day Month Year", "DAY MON YEAR"
        )
    # this (English) "formats" must agree with "_display_gregorian" (above)

    def __init__(self, format=None):
        """
        Create a DateDisplay class that converts a Date object to a string
        of the desired format. The format value must correspond to the format
        list value (DateDisplay.format[]).
        """

        DateDisplay.__init__(self, format)

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
            return "%sfrom %s to %s%s" % (qual_str, d1, d2, scal)
        elif mod == Date.MOD_RANGE:
            d1 = self.display_cal[cal](start)
            d2 = self.display_cal[cal](date.get_stop_date())
            scal = self.format_extras(cal, newyear)
            return "%sbetween %s and %s%s" % (qual_str, d1, d2, scal)
        else:
            text = self.display_cal[date.get_calendar()](start)
            scal = self.format_extras(cal, newyear)
            return "%s%s%s%s" % (qual_str, self._mod_str[mod], text, scal)
