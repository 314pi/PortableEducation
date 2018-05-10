
# common.py

"""
This module is an integeral part of the program
MMA - Musical Midi Accompaniment.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Bob van der Poel <bob@mellowood.ca>


These are a collection of miscellaneous routines used in various
parts of MMA. It is safe to load the whole works with:

    from MMA.common import *

without side effects (yeah, right).

"""

from random import randrange
import sys

import gbl


class struct:
    pass

def error(msg):
    """ Print an error message and exit.

        If the global line number is >=0 then print the line number
        as well.
    """

    ln = ""
    if gbl.lineno >= 0:
        ln += "<Line %d>" % gbl.lineno

    if gbl.inpath:
        ln += "<File:%s>" % gbl.inpath.fname

    if ln:
        ln += '\n'

    print "ERROR:%s     %s" % (ln, msg)

    sys.exit(1)


def warning(msg):
    """ Print warning message and return. """


    if gbl.noWarn:
        return

    ln = ""

    if gbl.lineno >= 0:
        ln = "<Line %d>" % gbl.lineno

    if gbl.inpath:
        ln += "<File:%s>" % gbl.inpath.fname

    print "Warning:%s\n        %s" % (ln, msg)



def getOffset(ticks, ran=None):
    """ Calculate a midi offset into a song.

        ticks == offset into the current bar.
        ran      == random adjustment from RTIME

        When calculating the random factor the test ensures
        that a note never starts before the start of the bar.
        This is important ... voice changes, etc. will be
        buggered if we put the voice change after the first
        note-on event.
    """

    p = gbl.tickOffset + int(ticks)     # int() cast is important!

    if ran:
        r = randrange( -ran, ran+1 )
        if ticks == 0 and r < 0:
            r=0
        p+=r

    return p



def stoi(s, errmsg=None):
    """ string to integer. """

    try:
        return int(s, 0)
    except:
        if errmsg:
            error(errmsg)
        else:
            error("Expecting integer value, not %s" % s)


def stof(s, errmsg=None):
    """ String to floating point. """

    try:
        return float(s)
    except:
        if errmsg:
            error(errmsg)
        else:
            error("Expecting a  value, not %s" % s)




def printList(l):
    """ Print each item in a list. Works for numeric and string."""

    for a in l:
        print a,
    print



def pextract(s, open, close, onlyone=None):
    """ Extract a parenthesized set of substrings.

    s        - original string
    open    - substring start tag \ can be multiple character
    close   - substring end tag   / strings (ie. "<<" or "-->")
    onlyone - optional, if set only the first set is extracted

    returns ( original sans subs, [subs, ...] )

    eg: pextract( "x{123}{666}y", '{',    '}' )
        Returns:  ( 'xy', [ '123', '666' ] )

    """

    subs =[]
    while 1:
        lstart = s.find(open)
        lend   = s.find(close)

        if lstart>-1 and lstart < lend:
            subs.append( s[lstart+len(open):lend].strip() )
            s = s[:lstart] + s[lend+len(close):]
            if onlyone:
                break
        else:
            break

    return s.strip(), subs

