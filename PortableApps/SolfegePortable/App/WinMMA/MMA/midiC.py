# midiC.py

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

This module contains interface for MIDI constants and conversion routines.
"""

from MMA.common import *
from MMA.miditables import *

def drumToValue(name):
    """ Get the value of the drum tone (-1==error). """

    try:
        v=int(name, 0)
    except:
        try:
            v = upperDrumNames.index(name.upper()) + 27
        except ValueError:
            error("Expecting a valid drum name or value for drum tone, not '%s'" % name)

    if v <0 or v > 127:
        error("Note in Drum Tone list must be 0..127, not %s" % v)

    return v


def instToValue(name):
    """ Get the value of the instrument name (-1==error). """

    try:
        return    upperVoiceNames.index(name.upper())
    except ValueError:
        return    -1

def ctrlToValue(name):
    """ Get the value of the controler name (-1==error). """

    try:
        return    upperCtrlNames.index(name.upper())
    except ValueError:
        return    -1

def valueToInst(val):
    """ Get the name of the inst. (or 'ERR'). """

    try:
        return    voiceNames[val]
    except IndexError:
        return "ERROR"


def valueToDrum(val):
    """ Get the name of the drum tone.

        We return the NAME of the tone, or the original value if there is
        no name associated with the value (only value 27 to 86 have names).
    """

    if val<27 or val>86:
        return str(val)
    else:
        return    drumNames[val-27]

def valueToCtrl(val):
    """ Get the name of the controller (or 'ERR'). """

    try:
        return    ctrlNames[val]
    except IndexError:
        return "ERROR"
