# -*- coding: iso-8859-1 -*- 
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2005  Donald N. Allingham
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

import locale
import constfunc

"""
Some OS environments do not support the locale.nl_langinfo() method
of determing month names and other date related information.

If nl_langinfo fails, that means we have to resort to shinanigans with
strftime.

Since these routines return values encoded into selected character
set, we have to convert to unicode.
"""

try:
    codeset = locale.nl_langinfo(locale.CODESET)

    month_to_int = {
        unicode(locale.nl_langinfo(locale.MON_1),codeset).lower()   : 1,
        unicode(locale.nl_langinfo(locale.ABMON_1),codeset).lower() : 1,
        unicode(locale.nl_langinfo(locale.MON_2),codeset).lower()   : 2,
        unicode(locale.nl_langinfo(locale.ABMON_2),codeset).lower() : 2,
        unicode(locale.nl_langinfo(locale.MON_3),codeset).lower()   : 3,
        unicode(locale.nl_langinfo(locale.ABMON_3),codeset).lower() : 3,
        unicode(locale.nl_langinfo(locale.MON_4),codeset).lower()   : 4,
        unicode(locale.nl_langinfo(locale.ABMON_4),codeset).lower() : 4,
        unicode(locale.nl_langinfo(locale.MON_5),codeset).lower()   : 5,
        unicode(locale.nl_langinfo(locale.ABMON_5),codeset).lower() : 5,
        unicode(locale.nl_langinfo(locale.MON_6),codeset).lower()   : 6,
        unicode(locale.nl_langinfo(locale.ABMON_6),codeset).lower() : 6,
        unicode(locale.nl_langinfo(locale.MON_7),codeset).lower()   : 7,
        unicode(locale.nl_langinfo(locale.ABMON_7),codeset).lower() : 7,
        unicode(locale.nl_langinfo(locale.MON_8),codeset).lower()   : 8,
        unicode(locale.nl_langinfo(locale.ABMON_8),codeset).lower() : 8,
        unicode(locale.nl_langinfo(locale.MON_9),codeset).lower()   : 9,
        unicode(locale.nl_langinfo(locale.ABMON_9),codeset).lower() : 9,
        unicode(locale.nl_langinfo(locale.MON_10),codeset).lower()  : 10,
        unicode(locale.nl_langinfo(locale.ABMON_10),codeset).lower(): 10,
        unicode(locale.nl_langinfo(locale.MON_11),codeset).lower()  : 11,
        unicode(locale.nl_langinfo(locale.ABMON_11),codeset).lower(): 11,
        unicode(locale.nl_langinfo(locale.MON_12),codeset).lower()  : 12,
        unicode(locale.nl_langinfo(locale.ABMON_12),codeset).lower(): 12,
       }

    long_months = (
        "",
        unicode(locale.nl_langinfo(locale.MON_1),codeset),
        unicode(locale.nl_langinfo(locale.MON_2),codeset),
        unicode(locale.nl_langinfo(locale.MON_3),codeset),
        unicode(locale.nl_langinfo(locale.MON_4),codeset),
        unicode(locale.nl_langinfo(locale.MON_5),codeset),
        unicode(locale.nl_langinfo(locale.MON_6),codeset),
        unicode(locale.nl_langinfo(locale.MON_7),codeset),
        unicode(locale.nl_langinfo(locale.MON_8),codeset),
        unicode(locale.nl_langinfo(locale.MON_9),codeset),
        unicode(locale.nl_langinfo(locale.MON_10),codeset),
        unicode(locale.nl_langinfo(locale.MON_11),codeset),
        unicode(locale.nl_langinfo(locale.MON_12),codeset),
        )

    short_months = (
        "",
        unicode(locale.nl_langinfo(locale.ABMON_1),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_2),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_3),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_4),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_5),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_6),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_7),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_8),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_9),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_10),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_11),codeset),
        unicode(locale.nl_langinfo(locale.ABMON_12),codeset),
        )

    # Gramps day number: Sunday => 1, Monday => 2, etc
    # "Return name of the n-th day of the week. Warning:
    #  This follows the US convention of DAY_1 being Sunday,
    #  not the international convention (ISO 8601) that Monday
    #  is the first day of the week."
    # see http://docs.python.org/library/locale.html
    long_days = (
        "",
        unicode(locale.nl_langinfo(locale.DAY_1),codeset), # Sunday
        unicode(locale.nl_langinfo(locale.DAY_2),codeset), # Monday
        unicode(locale.nl_langinfo(locale.DAY_3),codeset), # Tuesday
        unicode(locale.nl_langinfo(locale.DAY_4),codeset), # Wednesday
        unicode(locale.nl_langinfo(locale.DAY_5),codeset), # Thursday
        unicode(locale.nl_langinfo(locale.DAY_6),codeset), # Friday
        unicode(locale.nl_langinfo(locale.DAY_7),codeset), # Saturday
        )

    short_days = (
        "",
        unicode(locale.nl_langinfo(locale.ABDAY_1),codeset), # Sunday
        unicode(locale.nl_langinfo(locale.ABDAY_2),codeset), # Monday
        unicode(locale.nl_langinfo(locale.ABDAY_3),codeset), # Tuesday
        unicode(locale.nl_langinfo(locale.ABDAY_4),codeset), # Wednesday
        unicode(locale.nl_langinfo(locale.ABDAY_5),codeset), # Thursday
        unicode(locale.nl_langinfo(locale.ABDAY_6),codeset), # Friday
        unicode(locale.nl_langinfo(locale.ABDAY_7),codeset), # Saturday
        )

    tformat = locale.nl_langinfo(locale.D_FMT).replace('%y','%Y')
    # GRAMPS treats dates with '-' as ISO format, so replace separator on 
    # locale dates that use '-' to prevent confict
    tformat = tformat.replace('-', '/') 

except:
    import time

    if constfunc.win() or constfunc.mac():
        codeset = locale.getlocale()[1]
    else:
        codeset = locale.getpreferredencoding()

    month_to_int = {
        unicode(time.strftime('%B',(0,1,1,1,1,1,1,1,1)),codeset).lower() : 1,
        unicode(time.strftime('%b',(0,1,1,1,1,1,1,1,1)),codeset).lower() : 1,
        unicode(time.strftime('%B',(0,2,1,1,1,1,1,1,1)),codeset).lower() : 2,
        unicode(time.strftime('%b',(0,2,1,1,1,1,1,1,1)),codeset).lower() : 2,
        unicode(time.strftime('%B',(0,3,1,1,1,1,1,1,1)),codeset).lower() : 3,
        unicode(time.strftime('%b',(0,3,1,1,1,1,1,1,1)),codeset).lower() : 3,
        unicode(time.strftime('%B',(0,4,1,1,1,1,1,1,1)),codeset).lower() : 4,
        unicode(time.strftime('%b',(0,4,1,1,1,1,1,1,1)),codeset).lower() : 4,
        unicode(time.strftime('%B',(0,5,1,1,1,1,1,1,1)),codeset).lower() : 5,
        unicode(time.strftime('%b',(0,5,1,1,1,1,1,1,1)),codeset).lower() : 5,
        unicode(time.strftime('%B',(0,6,1,1,1,1,1,1,1)),codeset).lower() : 6,
        unicode(time.strftime('%b',(0,6,1,1,1,1,1,1,1)),codeset).lower() : 6,
        unicode(time.strftime('%B',(0,7,1,1,1,1,1,1,1)),codeset).lower() : 7,
        unicode(time.strftime('%b',(0,7,1,1,1,1,1,1,1)),codeset).lower() : 7,
        unicode(time.strftime('%B',(0,8,1,1,1,1,1,1,1)),codeset).lower() : 8,
        unicode(time.strftime('%b',(0,8,1,1,1,1,1,1,1)),codeset).lower() : 8,
        unicode(time.strftime('%B',(0,9,1,1,1,1,1,1,1)),codeset).lower() : 9,
        unicode(time.strftime('%b',(0,9,1,1,1,1,1,1,1)),codeset).lower() : 9,
        unicode(time.strftime('%B',(0,10,1,1,1,1,1,1,1)),codeset).lower() : 10,
        unicode(time.strftime('%b',(0,10,1,1,1,1,1,1,1)),codeset).lower() : 10,
        unicode(time.strftime('%B',(0,11,1,1,1,1,1,1,1)),codeset).lower() : 11,
        unicode(time.strftime('%b',(0,11,1,1,1,1,1,1,1)),codeset).lower() : 11,
        unicode(time.strftime('%B',(0,12,1,1,1,1,1,1,1)),codeset).lower() : 12,
        unicode(time.strftime('%b',(0,12,1,1,1,1,1,1,1)),codeset).lower() : 12,
       }

    long_months = (
        "",
        unicode(time.strftime('%B',(0,1,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,2,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,3,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,4,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,5,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,6,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,7,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,8,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,9,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,10,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,11,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%B',(0,12,1,1,1,1,1,1,1)),codeset),
       )

    short_months = (
        "",
        unicode(time.strftime('%b',(0,1,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,2,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,3,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,4,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,5,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,6,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,7,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,8,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,9,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,10,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,11,1,1,1,1,1,1,1)),codeset),
        unicode(time.strftime('%b',(0,12,1,1,1,1,1,1,1)),codeset),
       )

    # Gramps day number: Sunday => 1, Monday => 2, etc
    # strftime takes a (from the doc of standard Python library "time")
    #  "tuple or struct_time representing a time as returned by gmtime()
    #   or localtime()"
    # see http://docs.python.org/library/time.html
    # The seventh tuple entry returned by gmtime() is the day-of-the-week
    # number. tm_wday => range [0,6], Monday is 0
    # Note. Only the seventh tuple entry matters. The others are
    # just a dummy.
    long_days = (
        "",
        unicode(time.strftime('%A',(0,1,1,1,1,1,6,1,1)),codeset), # Sunday
        unicode(time.strftime('%A',(0,1,1,1,1,1,0,1,1)),codeset), # Monday
        unicode(time.strftime('%A',(0,1,1,1,1,1,1,1,1)),codeset), # Tuesday
        unicode(time.strftime('%A',(0,1,1,1,1,1,2,1,1)),codeset), # Wednesday
        unicode(time.strftime('%A',(0,1,1,1,1,1,3,1,1)),codeset), # Thursday
        unicode(time.strftime('%A',(0,1,1,1,1,1,4,1,1)),codeset), # Friday
        unicode(time.strftime('%A',(0,1,1,1,1,1,5,1,1)),codeset), # Saturday
        )

    short_days = (
        "",
        unicode(time.strftime('%a',(0,1,1,1,1,1,6,1,1)),codeset), # Sunday
        unicode(time.strftime('%a',(0,1,1,1,1,1,0,1,1)),codeset), # Monday
        unicode(time.strftime('%a',(0,1,1,1,1,1,1,1,1)),codeset), # Tuesday
        unicode(time.strftime('%a',(0,1,1,1,1,1,2,1,1)),codeset), # Wednesday
        unicode(time.strftime('%a',(0,1,1,1,1,1,3,1,1)),codeset), # Thursday
        unicode(time.strftime('%a',(0,1,1,1,1,1,4,1,1)),codeset), # Friday
        unicode(time.strftime('%a',(0,1,1,1,1,1,5,1,1)),codeset), # Saturday
        )

    # depending on the locale, the value returned for 20th Feb 2009 could be 
    # of the format '20/2/2009', '20/02/2009', '20.2.2009', '20.02.2009', 
    # '20-2-2009', '20-02-2009', '2009/02/20', '2009.02.20', '2009-02-20', 
    # '09-02-20' hence to reduce the possible values to test, make sure month 
    # is double digit also day should be double digit, prefebably greater than
    # 12 for human readablity

    timestr = time.strftime('%x',(2005,10,25,1,1,1,1,1,1)) 
    
    # GRAMPS treats dates with '-' as ISO format, so replace separator on 
    # locale dates that use '-' to prevent confict
    timestr = timestr.replace('-', '/') 
    time2fmt_map = {
        '25/10/2005' : '%d/%m/%Y',
        '10/25/2005' : '%m/%d/%Y',
        '2005/10/25' : '%Y/%m/%d',
        '25.10.2005' : '%d.%m.%Y',
        '10.25.2005' : '%m.%d.%Y',
        '2005.10.25' : '%Y.%m.%d',
        }
    
    try:
        tformat = time2fmt_map[timestr]
    except KeyError, e:
        tformat = '%d/%m/%Y'  #default value
