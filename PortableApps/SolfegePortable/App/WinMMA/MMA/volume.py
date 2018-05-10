
# volume.py

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

"""

from MMA.common import *


""" Volumes are specified in musical terms, but converted to
    midi velocities. This table has a list of percentage changes
    to apply to the current volume. Used in both track and global
    situations. Note that the volume for 'ffff' is 200%--this will
    most likely generate velocities outside the midi range of 0..127.
    But that's fine since mma will adjust volumes into the valid
    range. Using very high percentages will ensure that 'ffff' notes
    are (most likely) sounded with a maximum velocity.
"""

vols={ 'OFF': 0.00,  'PPPP': 0.05,  'PPP':  0.10,
       'PP':  0.25,  'P':    0.40,  'MP':   0.70,
       'M':   1.00,  'MF':   1.10,  'F':    1.30,
       'FF':  1.60,  'FFF':  1.80,  'FFFF': 2.00  }

volume = vols['M']        # default global volume
lastVolume = volume
futureVol = []
vTRatio = .6
vMRatio = 1-vTRatio


def adjvolume(ln):
    """ Adjust the ratio used in the volume table and track/global ratio. """

    global vols, vTRatio, vMRatio

    if not ln:
        error("Use: AdjustVolume DYN=RATIO [..]")

    for l in ln:

        try:
            v,r = l.split('=')
        except:
            error("AdjustVolume expecting DYN=RATIO pair, not '%s'" % l)

        v=v.upper()

        if v == 'RATIO':

            r=stof(r)

            if r<0 or r>100:
                error("VolumeRatio must be value 0 to 100")

            vTRatio = r/100
            vMRatio = 1-vTRatio

        elif v in vols:
            vols[v] = calcVolume(r, vols[v])

        else:
            error("Dynamic '%s' for AdjustVolume is unknown" % v )



    if gbl.debug:
        print "Volume Ratio: %s%% Track / %s%% Master" % ( vTRatio * 100, vMRatio * 100)
        print "Volume table:",
        for a in vols:
            print "%s=%s" % (a, int(vols[a] * 100)),
        print



def calcVolume(new, old):
    """ Calculate a new volume "new" possibly adjusting from "old". """

    if new[0] == '-' or new[0] == '+':
        a = stoi(new, "Volume expecting value for %% adjustment, not %s" % new)
        v = old + (old * a/100.)

    elif new[0] in "0123456789":
        v = stoi(new, "Volume expecting value, not '%s'" % new) / 100.

    else:
        new = new.upper()

        adj = None

        if '+' in new:
            new,adj = new.split('+')
        elif '-' in new:
            new,adj = new.split('-')
            adj = '-' + adj

        if not new in vols:
            error("Unknown volume '%s'" % new)

        v=vols[new]

        if adj:
            a = stoi(adj, "Volume expecting adjustment value, not %s" % adj)
            v += (v * (a/100.))

    return v


def setVolume(ln):
    """ Set master volume. """

    global volume, lastVolume

    lastVolume = volume

    if len(ln) != 1:
        error ("Use: Volume DYNAMIC")

    volume = calcVolume(ln[0], volume)

    if gbl.debug:
        print "Volume: %s%%" % volume


# The next 2 are called from the parser.

def setCresc(ln):
    setCrescendo(1, ln)

def setDecresc(ln):
    setCrescendo(-1, ln)


def setCrescendo(dir, ln):
    """ Combined (de)cresc() """

    global futureVol, volume, lastVolume

    lastVolume = volume

    if len(ln) not in (2, 3):
        error("Usage: (De)Cresc [start-Dynamic] final-Dynamic bar-count")

    if len(ln) == 3:
        setVolume([ln[0]])
        ln=ln[1:]

    futureVol = fvolume(dir, volume, ln)


# Used by both the 2 funcs above and from TRACK.setCresc()

def fvolume(dir, startvol, ln):
    """ Create a list of future vols. Called by (De)Cresc. """

    # Get destination volume

    destvol = calcVolume(ln[0], startvol)

    bcount = stoi(ln[1], "Type error in bar count for (De)Cresc, '%s'" % ln[1] )

    if bcount <= 0:
        error("Bar count for (De)Cresc must be postive")

    if dir > 0 and destvol < startvol:
        warning("Cresc volume less than current setting" )

    elif dir < 0 and destvol > startvol:
        warning("Decresc volume greater than current setting" )

    elif destvol == startvol:
        warning("(De)Cresc volume equal to current setting" )

    bcount -= 1
    step = ( destvol-startvol ) / bcount

    volList=[startvol]

    for a in range(bcount-1):
        startvol += step
        volList.append( startvol)

    volList.append(destvol)

    return volList




