# globals.py

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

import os

version = "1.1"        # Version -- March 7/2007

""" mtrks is storage for the MIDI data as it is created.
    It is a dict of class Mtrk() instances. Keys are the
    midi channel numbers. Ie, mtrks[2]    is for channel 2,
    etc. mtrks[0] is for the meta stuff.
"""

mtrks = {}

""" tnames is a dict of assigned track names. The keys are
    the track names; each entry is a pattern class instance.
    We have tnames['BASS-FOO'], etc.
"""

tnames = {}

""" midiAssigns keeps track of channel/track assignments. The keys
    are midi channels (1..16), the data is a list of tracks assigned
    to each channel. The tracks are only added, not deleted. Right
    now this is only used in -c reporting.
"""

midiAssigns={}
for c in range(0,17):
    midiAssigns[c]=[]

""" midiAvail is a list with each entry representing a MIDI channel.
    As channels are allocated/deallocated the appropriated slot
    is inc/decremented.
"""

midiAvail=[ 0 ] * 17   # slots 0..16, slot 0 is not used.

deletedTracks = []    # list of deleted tracks for -c report

""" This is a user constructed list of names/channels. The keys
    are names, data is a channel. Eg. midiChPrefs['BASS-SUS']==9
"""

midiChPrefs={}



""" Groove storage. Each entry in settingsGroove{} has a keyname
    of a saved groove.

    lastGroove and currentGroove are used by macros
"""

settingsGroove    = {}
lastGroove = ''
currentGroove = ''


""" SeqRnd variable is a list. The first entry is a flag:(0, 1 or x):
      0 - not set
      1 - set
      2 - set for specific tracks, track list starts at position [1]
"""

seqRnd = [0]       # set if SEQRND has been set


############# String constants ####################


ext = ".mma"        # extension for song/lib files.


##############  Tempo, and other midi positioning.  #############


BperQ       =  192    # midi ticks per quarter note
QperBar       =  4        # Beats/bar, set with TIME
tickOffset =  0        # offset of current bar in ticks
tempo       =  120    # current tempo
seqSize       =  1        # variation sequence table size
seqCount   =  0        # running count of variation

transpose  =  0        # Transpose is global (ignored by drum tracks)

lineno       = -1        # used for error reporting

swingMode  =  0     # defaults to 0, set to 1 for swing mode
swingSkew  =  None  # this is just for $_SwingMode macro

barNum     =  0     # Current line number

synctick   =  0     # flag, set if we want a tick on all tracks at offset 0

#############   Path and search variables. #############


libPath = ''
for     p in ( "c:\\mma\\lib", "/usr/local/share/mma/lib", "/usr/share/mma/lib", "./lib"):
    if os.path.isdir(p):
        libPath=p
        break

incPath = ''
for p in ( "c:\\mma\\includes", "/usr/local/share/mma/includes",
               "/usr/share/mma/includes", "./includes"):
    if os.path.isdir(p):
        incPath=p
        break

autoLib = 'stdlib'

outPath    =   ''      # Directory for MIDI file
mmaStart   =   []      # list of START files
mmaEnd     =   []      # list of END files
mmaRC      =   None    # user specified RC file, overrides defaults
inpath     =   None    # input file

midiFileType   = 1      # type 1 file, SMF command can change to 0
runningStatus  = 1      # running status enabled


#############  Options. #############


""" These variables are all set from the command line in MMA.opts.py.
    It's a bit of an easy-way-out to have them all here, but I don't think
    it hurts too much.
"""

debug          =     Ldebug = 0
pshow          =     Lpshow = 0
seqshow        =     Lseqshow = 0
showrun        =     Lshowrun = 0
noWarn         =     LnoWarn = 0
noOutput       =     LnoOutput = 0
showExpand     =     LshowExpand = 0
showFilenames  =     LshowFilenames = 0
chshow         =     Lchshow = 0

outfile        =     None
infile         =     None
docs           =     0
maxBars        =     500
makeGrvDefs    =     0
cmdSMF         =     None


