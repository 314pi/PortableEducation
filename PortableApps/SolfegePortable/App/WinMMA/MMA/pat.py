
# pat.py

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


import copy
import random
import math

import gbl
from   MMA.common import *
from   MMA.notelen import getNoteLen
import MMA.translate
import MMA.midi
import MMA.midiC
import MMA.alloc
import MMA.mdefine
import MMA.volume

class Voicing:
    def __init__(self):
        self.mode     = None
        self.range     = 12
        self.center     = 4
        self.random     = 0
        self.percent = 0
        self.bcount     = 0
        self.dir     = 0


def seqBump(l):
    """ Expand/contract an existing sequence list to the current seqSize."""

    while len(l) < gbl.seqSize:
        l += l
    return l[:gbl.seqSize]

pats = {}        # Storage for all pattern defines


class PC:
    """ Pattern class.

    Define classes for processing drum, chord, arp, and chord track.
    These are mostly the same, so we create a base class and derive
    the others from it.

    We have a class for each track type. They are all derived
    from the base 'Pats' class. These classes do special processing
    like parsing a pattern tuple and creating a chord.

    No functions ever link to the code in this module, it is
    only included into the real track class modules.

    """

    def __init__(self, nm):

        self.inited = 0
        self.name = nm
        self.channel = 0
        self.grooves = {}
        self.saveVols = {}
        self.ssvoice = -1     # Track the voice set for the track
        self.smidiVoice = () # Track MIDIVoice cmds to avoid dups
        self.midiSent = 0     # if set, MIDICLEAR invoked.


        """ Midi commands like Pan, Glis, etc. are stacked until musical
            data is actually written to the track. Each item in
            the midiPending list is a name (PAN, GLIS, etc), timeoffset, value.
        """

        self.midiPending = []

        self.riff = []

        self.disable = 0

        self.clearSequence()
        

        self.inited = 1


    ##########################################
    ## These are called from process() to set options

    def setCompress(self, ln):
        """ set/unset the compress flag. """

        ln=self.lnExpand(ln, 'Compress')

        tmp = []

        for n in ln:

            n = stoi(n, "Argument for %s Compress must be a value" \
                    % self.name)

            if n < 0 or n > 5:
                error("Compress %s out-of-range; must be 0 to 5" % n)

            if n and self.vtype=='CHORD' and self.voicing.mode:
                vwarn = 1

            tmp.append(n)

        self.compress = seqBump(tmp)

        if self.vtype not in ("CHORD", "ARPEGGIO"):
            warning ("Compress is ignored in %s tracks" % self.vtype)

        if gbl.debug:
            print "Set %s Compress to:" % self.name,
            printList(self.compress)


    def setRange(self, ln):
        """ set range. """

        ln=self.lnExpand(ln, 'Range')

        tmp = []

        for n in ln:

            n = stof(n)
            if n == 0:
                n=1
            if  n <= 0 or n >= 6:
                error("Range %s out-of-range; must be between 0..6, not %s" % (self.name, n))

            tmp.append(n)

        self.chordRange = seqBump(tmp)

        if self.vtype not in ("SCALE", "ARPEGGIO", "ARIA"):
            warning ("Range ignored in '%s' tracks" % self.vtype)

        if gbl.debug:
            print "Set %s Range to:" % self.name,
            printList(self.chordRange)


    def setVoicing(self, ln):
        """ set the Voicing Mode options.


            This is a stub. The real code is in patChord.py (settings are
            only valid for that type). """

        error("Voicing is not supported for %s tracks" % self.vtype)



    def setForceOut(self):
        """ Set the force output flag. This does 2 things: assigns
            a midi channel and sends the voicing setting to the track.
        """

        if not self.channel:
            self.setChannel()
        self.clearPending()

        self.insertVoice()


    def setDupRoot(self, ln):
        """ set/unset root duplication.

            This is a stub. Only valid for CHORDs and that is where the code is."""


        warning("RootDup has no effect in %s tracks" % self.vtype)


    def setChordLimit(self, ln):
        """ set/unset the chordLimit flag. """

        n = stoi(ln, "Argument for %s ChordLimit must be a value"     % self.name)

        if n < 0 or n > 8:
            error("ChordLimit %s out-of-range; must be 0 to 8" % n)

        self.chordLimit = n

        if self.vtype not in ("CHORD", "ARPEGGIO"):
            warning ("Limit is ignored in %s tracks" % self.vtype)

        if gbl.debug:
            print "Set %s ChordLimit to %s" % (self.name, n)


    def setChannel(self, ln=None):
        """ Set the midi-channel number for a track.

        - Checks for channel duplication
        - Auto assigns channel number if ln==''


        If no track number was passed, then we try to
        auto-alloc a track. First, we see if a preference
        was set via MidiChPref. If these is no preference,
        or if the preferred channel is already allocated
        we go though the list, top to bottom, to find
        an available channel.
        """

        if not ln:
            try:
                c=gbl.midiChPrefs[self.name]
            except:
                c=0

            if not c or gbl.midiAvail[c]:
                c=-1
                for a in range(16, 0, -1):
                    if a!=10 and not gbl.midiAvail[a]:
                        c=a
                        break

            if c < 0:
                error("No MIDI channel is available for %s,\n"
                      "Try CHShare or Delete unused tracks" % self.name)

        else:
            c = stoi(ln, "%s Channel assignment expecting Value, not %s" %
                (self.name, ln))

            if c<0 or c>16:
                error("%s Channel must be 0..16, not %s" % (self.name, ln))

        if c == 10:
            if self.vtype == 'DRUM':
                pass
            elif self.vtype in ('SOLO', 'MELODY') and self.drumType:
                pass
            else:
                error("Channel 10 is reserved for DRUM, not %s" % self.name)

        if self.vtype == 'DRUM' and c != 10:
            error("DRUM tracks must be assigned to channel 10")

        # Disable the channel.

        if c == 0:
            if gbl.midiAvail[self.channel]:
                gbl.midiAvail[self.channel] -= 1
            s="%s channel disabled" % self.name
            if gbl.midiAvail[self.channel]:
                s+=" Other tracks are still using channel %s" % self.channel
            else:
                s+=" Channel %s available" % self.channel
            warning(s)
            self.channel = 0
            self.disable = 1
            return


        if c != 10:
            for a, tr in gbl.tnames.items():
                if a == self.name:    # okay to reassign same number
                    continue

                if tr.channel == c:
                    error("Channel %s is assigned to %s" % (c, tr.name ) )

        self.channel = c
        if not self.name in gbl.midiAssigns[c]:
            gbl.midiAssigns[c].append(self.name)

        gbl.midiAvail[c]+=1

        if not c in gbl.mtrks:
            gbl.mtrks[c]=MMA.midi.Mtrk(c)
            offset=0
            if gbl.debug:
                print "MIDI channel %s buffer created" % c
        else:
            offset = gbl.tickOffset

        if c != 10:
            f=0
            for a, i in enumerate(self.midiPending):
                if i[0]=='TNAME':
                    f=1
            if not f:
                self.midiPending.append(('TNAME', 0, self.name.title() ))

        if gbl.debug:
            print "MIDI Channel %s assigned to %s" % (self.channel, self.name)


    def setChShare(self, ln):
        """ Share midi-channel setting. """

        if self.channel:    # If channel already assigned, ignore
            warning("Channel for %s has previously been assigned "
                "(can't ChShare)" % self.name)
            return

        """ Get name of track to share with and make sure it exists.
        If not, trackAlloc() will create the track. Do some
        sanity checks and ensure that the shared track has
        a channel assigned.
        """

        sc = ln.upper()

        MMA.alloc.trackAlloc(sc, 1)

        if not sc in gbl.tnames:
            error("Channel '%s' does not exist. No such name" % sc)

        if sc == self.name:
            error("%s can't share MIDI channel with itself" % sc)


        if not gbl.tnames[sc].channel:
            gbl.tnames[sc].setChannel()

        schannel = gbl.tnames[sc].channel

        if not schannel:
            error("CHShare attempted to assign MIDI channel for %s, but "
                    "none avaiable" %    self.name)


        """ Actually do the assignment. Also copy voice/octave from
            base track to this one ... it's going to use that voice anyway?
        """

        self.channel = schannel

        self.voice = gbl.tnames[sc].voice[:]
        self.octave = gbl.tnames[sc].octave[:]


        # Update the avail. lists

        gbl.midiAssigns[self.channel].append(self.name)
        gbl.midiAvail[self.channel]+=1


    def setChannelVolume(self, v):
        """ LowLevel MIDI command. Set Channel Voice. """

        self.midiPending.append(( "CVOLUME", gbl.tickOffset, v) )

        if gbl.debug:
            print "Set %s MIDIChannelVolume to %s" % (self.name, v)

    def setTname(self, n):
        """ Set the track name.

            This is stacked and only gets output if track generates MIDI.
            It is a handy way to override MMA's track naming.
        """

        self.midiPending.append(('TNAME', 0, n ))
        if gbl.debug:
            print "Set %s track name for MIDI to %s" % (self.name, n)

    def setPan(self, ln):
        """ Set MIDI Pan for this track. """

        v = stoi(ln[0], "Expecting integer value 0..127")

        if v<0 or v>127:
            error("PAN value must be 0..127")

        self.midiPending.append( ("PAN", gbl.tickOffset, v))

        if gbl.debug:
            print "Set %s MIDIPan to %s" % (self.name, v)



    def setGlis(self, ln):
        """ Set MIDI Glis for this track. """

        v = stoi(ln, "Expecting integer for Portamento")

        if v<0 or v>127:
            error("Value for Portamento must be 0..127")

        self.midiPending.append( ("GLIS", gbl.tickOffset, v))

        if gbl.debug:
            print "Set %s MIDIPortamento to %s" % (self.name, v)



    def setStrum(self, ln):
        """ Set Strum time. CHORD only option. """

        warning("Strum has no effect in %s tracks" % self.name)


    def setTone(self, ln):
        """ Set Tone. Error trap, only drum tracks have tone. """

        error("Tone command not supported for %s track" % self.name)


    def setOn(self):
        """ Turn ON track. """

        self.disable = 0
        self.ssvoice = -1

        if gbl.debug:
            print "%s Enabled" % self.name


    def setOff(self):
        """ Turn OFF track. """

        self.disable = 1

        if gbl.debug:
            print "%s Disabled" % self.name



    def setRVolume(self, ln):
        """ Set the volume randomizer for a track. """

        ln = self.lnExpand(ln, 'RVolume')
        tmp = []

        for n in ln:

            n = stoi(n, "Argument for %s RVolume must be a value"  % self.name)

            if n < 0 or n > 100:
                error("RVolume %s out-of-range; must be 0..100" % n)

            if n > 30:
                warning("%s is a large RVolume value!" % n)

            tmp.append( n/100. )

        self.rVolume = seqBump(tmp)

        if gbl.debug:
            print "Set %s Rvolume to:" % self.name,
            for n in self.rVolume:
                print int(n * 100),
            print


    def setRSkip(self, ln):
        """ Set the note random skip factor for a track. """

        ln = self.lnExpand(ln, 'RSkip')
        tmp = []

        for n in ln:
            n = stoi(n, "Expecting integer after in RSkip")

            if n < 0 or n > 99:
                error("RSkip arg must be 0..99")

            tmp.append(n/100.)

        self.rSkip = seqBump(tmp)

        if gbl.debug:
            print "Set %s RSkip to:" % self.name,
            for n in self.rSkip:
                print int(n * 100),
            print


    def setRTime(self, ln):
        """ Set the timing randomizer for a track. """

        ln=self.lnExpand(ln,  'RTime')
        tmp = []

        for n in ln:
            n=stoi(n, "Expecting an integer for Rtime")
            if n < 0 or n > 100:
                error("RTime %s out-of-range; must be 0..100" % n)

            tmp.append(n)

        self.rTime = seqBump(tmp)

        if gbl.debug:
            print "Set %s RTime to:" % self.name,
            printList(self.rTime)


    def setRnd(self, arg):
        """ Enable random pattern selection from sequence."""

        if arg in ("ON", "1"):
            self.seqRnd = 1

        elif arg in ("OFF", "0"):
            self.seqRnd = 0

        else:
            error("SeqRnd: '%s' is not a valid option" % arg)

        if gbl.debug:
            if self.seqRnd:
                a="On"
            else:
                a="Off"
            print "%s SeqRnd: %s" % (self.name, a)


    def setRndWeight(self, ln):
        """ Set weighting factors for seqrnd. """

        ln = self.lnExpand(ln, "SeqRndWeight")
        tmp = []

        for n in ln:
            n = stoi(n)
            if n < 0: error("SeqRndWeight: Values must be 0 or greater")
            tmp.append(n)

        self.seqRndWeight = seqBump(tmp)

        if gbl.debug:
            print "%s SeqRndWeight:" % self.name,
            printList(self.seqRndWeight)


    def setDirection(self, ln):
        """ Set scale direction. """

        ln = self.lnExpand(ln, "Direction")
        tmp = []

        for n in ln:
            n = n.upper()
            if not n in ('UP', 'DOWN', 'BOTH', 'RANDOM'):
                error("Unknown %s Direction '%s'"  % (self.name, n) )
            tmp.append(n)

        self.direction = seqBump(tmp)

        if self.vtype == 'SCALE':
            self.lastChord = None
            self.lastNote = -1


        if gbl.debug:
            print "Set %s Direction to:" % self.name,
            printList(self.direction)


    def setScaletype(self, ln):
        """ Set scale type.

            This is a error stub. The real code is in the permitted track code.
        """

        warning("ScaleType has no effect in %s tracks") % self.vtype


    def setInvert(self, ln):
        """ Set inversion for track.

            This can be applied to any track,
            but has no effect in drum tracks. It inverts the chord
            by one rotation for each value.
        """

        ln=self.lnExpand(ln, "Invert")

        vwarn = 0
        tmp = []

        for n in ln:
            n = stoi(n, "Argument for %s Invert must be an integer" % self.name)

            if n and self.vtype=='CHORD' and self.voicing.mode:
                vwarn = 1

            tmp.append(n)

        self.invert = seqBump(tmp)

        if self.vtype not in ("CHORD", "ARPEGGIO"):
            warning ("Invert is ignored in %s tracks" % self.vtype)

        if vwarn:
            warning("Setting both Voicing Mode and Invert is not a good idea")

        if gbl.debug:
            print "Set %s Invert to:" % self.name,
            printList(self.invert)


    def setOctave(self, ln):
        """ Set the octave for a track. """

        ln=self.lnExpand(ln, 'Octave')
        tmp = []

        for n in ln:
            n = stoi(n, "Argument for %s Octave must be an integer"  % self.name)
            if n < 0 or n > 10:
                error("Octave %s out-of-range; must be 0..10" % n)

            tmp.append( n * 12 )

        self.octave = seqBump(tmp)

        if gbl.debug:
            print "Set %s Octave to:" % self.name,
            for i in self.octave:
                print i/12,
            print


    def setSpan(self, start, end):
        """ Set span.

            Note: The start/end parm has been verified in parser.

        """

        if self.vtype == 'DRUM':
            warning("Span has no effect in Drum tracks")

        self.spanStart = start
        self.spanEnd = end

        if gbl.debug:
            print "Set %s Span to %s...%s" % (self.name, self.spanStart, self.spanEnd)


    def setHarmony(self, ln):
        """ Set the harmony. """

        ln=self.lnExpand(ln, 'Harmony')
        tmp = []

        for n in ln:
            n = n.upper()
            if n in ( '-', '-0', 'NONE'):
                n = None

            tmp.append(n)

        self.harmony = seqBump(tmp)

        if self.vtype in ( 'CHORD', 'DRUM' ):
            warning("Harmony setting for %s track ignored" % self.vtype)

        if gbl.debug:
            print "Set %s Harmony to:" % self.name,
            printList(self.harmony)


    def setHarmonyOnly(self, ln):
        """ Set the harmony only. """


        ln=self.lnExpand(ln, 'HarmonyOnly')
        tmp = []

        for n in ln:
            n = n.upper()
            if n in ('-', '0'):
                n = None

            tmp.append(n)

        self.harmony = seqBump(tmp)
        self.harmonyOnly = seqBump(tmp)

        if self.vtype in ( 'CHORD', 'DRUM'):
            warning("HarmonyOnly setting for %s track ignored" % self.vtype)

        if gbl.debug:
            print "Set %s HarmonyOnly to:" % self.name,
            printList(self.harmonyOnly)


    def setHarmonyVolume(self, ln):
        """ Set harmony volume adjustment. """

        ln=self.lnExpand(ln, 'HarmonyOnly')
        tmp = []

        for n in ln:
            v=stoi(n)

            if v<0:
                error("HarmonyVolume adjustment must be positive integer")
            tmp.append(v/100.)

        self.harmonyVolume = seqBump(tmp)

        if self.vtype in ( 'CHORD', 'DRUM' ):
            warning("HarmonyVolume adjustment for %s track ignored" % self.vtype)

        if gbl.debug:
            print "Set %s HarmonyVolume to:" % self.name,
            printList(self.harmonyVolume)


    def setSeqSize(self):
        """ Expand existing pattern list. """

        self.sequence      = seqBump(self.sequence)
        if self.midiVoice:
            self.midiVoice = seqBump(self.midiVoice)
        if self.midiSeq:
            self.midiSeq   = seqBump(self.midiSeq)
        self.invert        = seqBump(self.invert)
        self.artic         = seqBump(self.artic)
        self.volume        = seqBump(self.volume)
        self.voice         = seqBump(self.voice)
        self.rVolume       = seqBump(self.rVolume)
        self.rSkip         = seqBump(self.rSkip)
        self.rTime         = seqBump(self.rTime)
        self.seqRndWeight  = seqBump(self.seqRndWeight)
        self.strum         = seqBump(self.strum)
        self.octave        = seqBump(self.octave)
        self.harmony       = seqBump(self.harmony)
        self.harmonyOnly   = seqBump(self.harmonyOnly)
        self.harmonyVolume = seqBump(self.harmonyVolume)
        self.direction     = seqBump(self.direction)
        self.scaleType     = seqBump(self.scaleType)
        self.compress      = seqBump(self.compress)
        self.chordRange    = seqBump(self.chordRange)
        self.dupRoot       = seqBump(self.dupRoot)
        self.unify         = seqBump(self.unify)
        self.accent        = seqBump(self.accent)

        if self.vtype == "DRUM":
            self.toneList  = seqBump(self.toneList)


    def setVoice(self, ln):
        """ Set the voice for a track.

        Note, this just sets flags, the voice is set in bar().
        ln[] is not nesc. set to the correct length.
        """

        ln=self.lnExpand(ln, 'Voice')
        tmp = []

        for n in ln:
            n = MMA.translate.vtable.get(n)
            a=MMA.midiC.instToValue(n)

            if a < 0:
                a=stoi(n, "Expecting a valid voice name or value, "
                       "not '%s'" % n)
                if a <0 or a > 127:
                    error("Voice must be 0..127")
            tmp.append( a )

        self.voice = seqBump(tmp)

        if self.channel and len(gbl.midiAssigns[self.channel])>1:           
            a=''
            for n in gbl.midiAssigns[self.channel]:
                if n != self.name:
                    a += ' %s' % n
            warning("Track %s is shared with %s,\n"
                "  changing voice may create conflict" % (a,self.name))


        if gbl.debug:
            print "Set %s Voice to:" % self.name,
            for a in self.voice:
                print MMA.midiC.valueToInst(a),
            print


    def setMidiClear(self, ln):
        """ Set MIDIclear sequences. """


        if ln[0] in 'zZ-':
            self.midiClear = None
        else:
            self.midiClear = MMA.mdefine.mdef.get(ln[0])

        if gbl.debug:
            print "%s MIDIClear: %s" % (self.name, self.midiSeqFmt(self.midiClear))


    def doMidiClear(self):
        """ Reset MIDI settings. """

        if self.midiSent:
            if    not self.midiClear:
                warning("%s: Midi data has been inserted with MIDIVoice/Seq "
                    "but no MIDIClear data is present" % self.name)

            else:
                for i in self.midiClear:
                    gbl.mtrks[self.channel].addCtl(gbl.tickOffset, i[1])

            self.midiSent = 0


    def setMidiSeq(self, ln):
        """ Set a midi sequence for a track.

        This is sent for every bar. Syntax is:
        <beat> <ctrl> hh .. ; ...

        or a single '-' to disable.
        """

        """ lnExpand() works here! The midi data has been converted to
             pseudo-macros already in the parser. """

        ln=self.lnExpand(ln, "MidiSeq")

        seq = []
        for a in ln:
            if a in 'zZ-':
                seq.append(None)
            else:
                seq.append(MMA.mdefine.mdef.get(a.upper()))

        if seq.count(None) == len(seq):
            self.midiSeq = []
        else:
            self.midiSeq = seqBump( seq )

        if gbl.debug:
            print "%s MIDISeq:" % self.name,
            for l in seq:
                print '{ %s }' % self.midiSeqFmt(l),



    def setMidiVoice(self, ln):
        """ Set a MIDI sequence for a track.

        This is sent whenever we send a VOICE. Syntax is:
        <beat> <ctrl> hh .. ; ...

        or a single '-' to disable.
        """

        """ lnExpand() works here! The midi data has been converted to
        pseudo-macros already in the parser. """

        ln = self.lnExpand(ln, 'MIDIVoice')

        seq = []
        for a in ln:
            if a in 'zZ':
                seq.append(None)
            else:
                seq.append(MMA.mdefine.mdef.get(a.upper()))

        if seq.count(None) == len(seq):
            self.midiVoice = []
        else:
            self.midiVoice = seqBump( seq )


        if gbl.debug:
            print "%s MIDIVoice:" % self.name,
            for l in seq:
                print '{ %s }' % self.midiSeqFmt(l),
            print


    def midiSeqFmt(self, lst):
        """ Used by setMidiVoice/Clear/Seq for debugging format. """

        if lst == None:
            return ''
        ret=''
        for i in lst:
            ret += "%s %s 0x%02x ; " % (i[0],
                MMA.midiC.valueToCtrl(ord(i[1][0])),
                ord(i[1][1]))
        return ret.rstrip("; ")


    def setVolume(self, ln):
        """ Set the volume for a pattern.
            ln - list of volume names (pp, mf, etc)
            ln[] not nesc. correct length
        """

        ln=self.lnExpand(ln, 'Volume')
        tmp = [None] * len(ln)

        for i,n in enumerate(ln):
            a = MMA.volume.calcVolume(n, self.volume[i])

            if self.vtype == 'DRUM':
                a=MMA.translate.drumVolTable.get(self.toneList[i], a)
            else:
                a=MMA.translate.voiceVolTable.get(self.voice[i], a)
            tmp[i] = a

        self.volume = seqBump(tmp)

        if gbl.debug:
            print "Set %s Volume to:" % self.name,
            for a in self.volume:
                print int(a * 100),
            print


    def setCresc(self, dir, ln):
        """ Set Crescendo for a track.     """

        if len(ln) == 3:
            self.setVolume([ln[0]])
            ln=ln[1:]

        vol = self.volume[0]

        if self.volume.count(vol) != len(self.volume):
            warning("(De)Crescendo being used with track with variable sequence volumes")

        self.futureVols = MMA.volume.fvolume(dir, vol, ln)


    def setMallet(self, ln):
        """ Mallet (repeat) settngs. """

        for l in ln:
            try:
                mode, val = l.upper().split('=')
            except:
                error("Each Mallet option must contain a '=', not '%s'" % l)

            if mode == 'RATE':
                self.mallet = getNoteLen(val)

            elif mode == 'DECAY':
                val = stof(val, "Mallet Decay must be a value, not '%s'" % val)

                if val < -50 or val > 50:
                    error("Mallet Decay rate must be -50..+50")

                self.malletDecay = val/100

        if gbl.debug:
            print "%s Mallet Rate:%s Decay:%s" % \
                (self.name, self.mallet, self.malletDecay)


    def setAccent(self, ln):
        """ Set the accent values. This is a list of lists, a list for each seq. """

        tmp = []


        """ We can do "Track Accent 1 20 3 -10" or "Track Accent {1 20 3 -10}"
        or even something like "Track Accent {1 20} / {/} {3 20}"
        Note that the "/" can or not have {}s.
        """

        ln = ' '.join(ln)
        if not ln.startswith('{'):
            ln='{' + ln +"}"

        # Convert string to list. One entry per seq.

        l=[]
        while ln:
            if not ln.startswith("{"):
                if ln[0]=='/':
                    l.append('/')
                    ln=ln[1:].strip()
                else:
                    error("Unknown value in %s Accent: %s" % (self.name, ln[0]))
            else:
                a,b = pextract(ln, "{", "}", 1)
                ln=a.strip()
                if len(b)==1 and b[0]=='/':
                    l.append('/')
                else:
                    l.append(b[0].split())


        ln=self.lnExpand(l, 'Accent')


        for l in ln:
            tt=[]
            if    len(l)/2*2 != len(l):
                error("Use: %s Accent Beat Percentage [...]" % self.name)

            for b, v in zip(l[::2], l[1::2]):
                b=self.setBarOffset( b )
                v=stoi(v, "Bbeat offset must be a value, not '%s'" % v)
                if v < -100 or v > 100:
                    error("Velocity adjustment (as percentage) must "
                          "be -100..100, not '%s'" % v)

                tt.append( (b, v/100. ) )
            tmp.append(tt)

        self.accent = seqBump( tmp )

        if gbl.debug:
            print "%s Accent:" % self.name,
            for s in self.accent:
                print "{",
                for b,v in s:
                    print '%s %s' % (1+(b/float(gbl.BperQ)), int(v*100)),
                print "}",
            print


    def setArtic(self, ln):
        """ Set the note articuation value. """

        ln=self.lnExpand(ln, 'Articulate')
        tmp = []

        for n in ln:
            a = stoi(n, "Expecting value in articulation setting")
            if a < 1 or a > 200:
                error("Articulation setting must be 1..200, not %s" % a)

            if a>150:
                warning("Large Articulate value: %s" % a)

            tmp.append(a)

        self.artic = seqBump(tmp)

        if gbl.debug:
            print "Set %s Articulate to:" % self.name,
            printList(self.artic)


    def setUnify(self, ln):
        """ Set unify. """

        ln = self.lnExpand(ln, "Unify")
        tmp = []

        for n in ln:
            n=n.upper()
            if n  in ( 'ON',  '1'):
                tmp.append(1)
            elif n in( 'OFF', '0'):
                tmp.append(0)
            else:
                error("Unify accepts ON | OFF | 0 | 1")

        self.unify = seqBump(tmp)

        if gbl.debug:
            print "Set %s Unify to:" % self.name,
            printList(self.unify)



    def lnExpand(self, ln, cmd):
        """ Validate and expand a list passed to a set command. """

        if len(ln) > gbl.seqSize:
            warning("%s list truncated to %s patterns" % (self.name, gbl.seqSize) )
            ln = ln[:gbl.seqSize]

        last = None

        for i,n     in enumerate(ln):
            if n == '/':
                if not last:
                    error ("You cannot use a '/' as the first item "
                           "in a %s list" % cmd)
                else:
                    ln[i] = last
            else:
                last = n

        return ln


    def copySettings(self, cp):
        """ Copy the voicing from a 2nd voice to the current one. """

        if not cp in gbl.tnames:
            error("CopySettings does not know track '%s'" % cp)

        cp=gbl.tnames[cp]

        if cp.vtype != self.vtype:
            error("Tracks must be of same type for copy ... "
                "%s and %s aren't" % (self.name, cp.name))

        self.volume      = cp.volume[:]
        self.rVolume     = cp.rVolume[:]
        self.accent      = cp.accent[:]
        self.rSkip       = cp.rSkip[:]
        self.rTime       = cp.rTime[:]
        self.strum       = cp.strum[:]
        self.octave      = cp.octave[:]
        self.harmony     = cp.harmony[:]
        self.harmonyOnly = cp.harmonyOnly[:]
        self.harmonyVolume = cp.harmonyVolume[:]
        self.direction   = cp.direction[:]
        self.scaleType   = cp.scaleType[:]
        self.voice       = cp.voice[:]
        self.invert      = cp.invert[:]
        self.artic       = cp.artic[:]
        self.compress    = cp.compress[:]

        self.riff        = cp.riff[:]

        if self.vtype == 'DRUM':
            self.toneList = cp.toneList[:]


        if gbl.debug:
            print "Settings from %s copied to %s" % (cp.name, self.name)



    ##################################################
    ## Save/restore grooves

    def saveGroove(self, gname):
        """ Define a groove.

            Called by the 'DefGroove Name'. This is called for

            each track.

            If 'gname' is already defined it is overwritten.

            Note aux. function which may be defined for each track type.
        """

        self.grooves[gname] = {
            'ACCENT':    self.accent[:],
            'ARTIC':     self.artic[:],
            'COMPRESS':  self.compress[:],
            'DIR':       self.direction[:],
            'DUPROOT':   self.dupRoot[:],
            'HARMONY':   self.harmony[:],
            'HARMONYO':  self.harmonyOnly[:],
            'HARMONYV':  self.harmonyVolume[:],
            'INVERT':    self.invert[:],
            'LIMIT':    self.chordLimit,
            'RANGE':    self.chordRange[:],
            'OCTAVE':    self.octave[:],
            'RSKIP':    self.rSkip[:],
            'RTIME':    self.rTime[:],
            'RVOLUME':    self.rVolume[:],
            'SCALE':    self.scaleType[:],
            'SEQ':        self.sequence[:],
            'SEQRND':    self.seqRnd,
            'SEQRNDWT': self.seqRndWeight[:],
            'STRUM':    self.strum[:],
            'VOICE':    self.voice[:],
            'VOLUME':    self.volume[:],
            'UNIFY':    self.unify[:],
            'MIDISEQ':    self.midiSeq[:],
            'MIDIVOICE':self.midiVoice[:],
            'MIDICLEAR':self.midiClear[:],
            'SPAN':     (self.spanStart, self.spanEnd),
            'MALLET':   (self.mallet, self.malletDecay),
        }


        if self.vtype == 'CHORD':
            self.grooves[gname]['VMODE'] =    copy.deepcopy(self.voicing)

        if self.vtype == 'DRUM':
            self.grooves[gname]['TONES'] = self.toneList[:]


    def restoreGroove(self, gname):
        """ Restore a defined groove. """

        self.doMidiClear()

        g = self.grooves[gname]

        self.sequence   =  g['SEQ']
        self.volume     =  g['VOLUME']
        self.accent     =  g['ACCENT']
        self.rTime      =  g['RTIME']
        self.rVolume    =  g['RVOLUME']
        self.rSkip      =  g['RSKIP']
        self.strum      =  g['STRUM']
        self.octave     =  g['OCTAVE']
        self.voice      =  g['VOICE']
        self.harmonyOnly=  g['HARMONYO']
        self.harmony    =  g['HARMONY']
        self.harmonyVolume = g['HARMONYV']
        self.direction  =  g['DIR']
        self.scaleType  =  g['SCALE']
        self.invert     =  g['INVERT']
        self.artic      =  g['ARTIC']
        self.seqRnd     =  g['SEQRND' ]
        self.seqRndWeight = g['SEQRNDWT']
        self.compress   =  g['COMPRESS']
        self.chordRange =  g['RANGE']
        self.dupRoot    =  g['DUPROOT']
        self.chordLimit =  g['LIMIT']
        self.unify      =  g['UNIFY']
        self.midiClear  =  g['MIDICLEAR']
        self.midiSeq    =  g['MIDISEQ']
        self.midiVoice  =  g['MIDIVOICE']
        self.spanStart, self.spanEnd  = g['SPAN']
        self.mallet, self.malletDecay = g['MALLET']

        if self.vtype == 'CHORD':
            self.voicing    =  g['VMODE']

        if self.vtype == 'DRUM':
            self.toneList = g['TONES']


        """ It's quite possible that the track was created after
            the groove was saved. This means that the data restored
            was just the default stuff inserted when the track
            was created ... which is fine, but the sequence size
            isn't necs. right. We can probably test any list, and octave[]
            is as good as any.
        """

        if len(self.octave) != gbl.seqSize:
            self.setSeqSize()

    ####################################
    ## Sequence functions

    def setSequence(self, ln):
        """ Set the sequence for a track.

            The ln passed from the parser should be a list of existing
            patterns, plus the special 'patterns' Z, z, -, and *. Remember
            that the parser has already converted {} patterns to a special
            pattern line _1.

            First we expand ln to the proper length. lnExpand() also
            duplicates '/' to the previous pattern.

            Then we step though ln:

              - convert 'z', 'Z' and '-' to empty patterns.

              - duplicate the existing pattern for '*'

              - copy the defined pattern for everything else.
                There's a bit of Python reference trickery here.
                Eg, if we have the line:

                   Bass Sequence B1 B2

                   the sequence is set with pointers to the existing
                patterns defined for B1 and B2. Now, if we later change
                the definitions for B1 or B2, the stored pointer DOEN'T
                change. So, changing pattern definitions has NO EFFECT.

        """


        ln=self.lnExpand(ln, 'Sequence')
        tmp = [None] * len(ln)

        for i, n in enumerate(ln):
            n=n.upper()

            if n in     ('Z', '-'):
                tmp[i] = None

            elif n == '*':
                tmp[i] = self.sequence[i]

            else:
                p= (self.vtype, n)
                if not p in pats:
                    error("Track %s does not have pattern '%s'" % p )
                tmp[i] = pats[p]

        self.sequence = seqBump(tmp)

        if gbl.seqshow:
            print "%s sequence set:" % self.name,
            for a in ln:
                if  a in "Zz-":
                    print "-",
                else:
                    print a,
            print


    def clearSequence(self):
        """ Clear sequence for track.

            This is also called from __init__() to set the initial defaults for each track.

        """

        if self.vtype != 'SOLO' or not self.inited:
            self.artic        =  [90]
            self.sequence     =  [None]
            self.seqRnd       =  0
            self.seqRndWeight =  [1]
            if self.vtype == 'ARIA':
                  self.scaleType = ['CHORD']
            else:
                  self.scaleType = ['AUTO']
            self.rVolume      =  [0]
            self.rSkip        =  [0]
            self.rTime        =  [0]
            self.octave       =  [4 * 12]
            self.voice        =  [0]
            self.chordRange   =  [1]
            self.harmony      =  [None]
            self.harmonyOnly  =  [None]
            self.harmonyVolume = [.8]
            self.strum        =  [0]
            self.volume       =  [MMA.volume.vols['M'] ]
            self.compress     =  [0]
            self.dupRoot      =  [0]
            self.chordLimit   =  0
            self.invert       =  [0]
            self.lastChord    =  []
            self.accent       =  [ [] ]
            self.unify        =  [0]
            self.midiClear    =  []
            self.midiSeq      =  []
            self.midiVoice    =  []
            self.spanStart    =  0
            self.spanEnd      =  127
            self.mallet       =  0
            self.malletDecay  =  0
            self.futureVols   =  []


        if self.riff:
            if len(self.riff) > 1:
                warning("%s sequence clear deleting %s riffs" % (self.name, len(self.riff)))
            else:
                warning("%s sequence clear deleting unused riff" % self.name )

        self.riff = []


        if self.vtype == 'CHORD':
            self.voicing   = Voicing()
            self.direction = ['UP']
        else:
            self.direction    =  ['BOTH']

        self.setSeqSize()


    ############################
    ### Pattern functions
    ############################


    def definePattern(self, name, ln):
        """ Define a Pattern.

        All patterns are stored in pats{}. The keys for this
        are tuples -- (track type, pattern name).

        """

        name = name.upper()
        slot = (self.vtype,name)

        # This is just for the debug code

        if name.startswith('_'):
            redef = "dynamic define"
        elif slot in pats:
            redef = name + ' redefined'
        else:
            redef = name + ' created'

        ln = ln.rstrip('; ')    # Delete optional trailing    ';' & WS
        pats[slot] = self.defPatRiff(ln)

        if gbl.pshow:
            print "%s pattern %s:" % (self.name.title(), redef )
            self.printPattern(pats[slot])


    def setRiff(self, ln):
        """ Define and set a Riff. """

        solo = self.vtype in ("MELODY", "SOLO")

        if solo:
            self.riff.append(ln)
        else:
            ln = ln.rstrip('; ')
            if len(ln) == 1 and (ln[0] in ('Z','z','-')):
                self.riff.append([])
            else:
                self.riff.append(self.defPatRiff(ln))

        if gbl.pshow:
            print "%s Riff:" % self.name,
            if solo:
                print self.riff[-1]
            else:
                self.printPattern(self.riff[-1])


    def defPatRiff(self, ln):
        """ Worker function to define pattern. Shared by definePattern()
        and setRiff().
        """

        def mulPatRiff(oldpat, fact):
            """ Multiply a pattern. """

            fact = stoi(fact, "The multiplier arg must be an integer not '%s'" % fact)

            if fact<1 or fact >100:
                error("The multiplier arg must be in the range 2 to 100")


            """ Make N copies of pattern, adjusted so that the new copy has
                all note lengths and start times  adjusted.
                  eg: [[1, 2, 66], [3, 2, 88]]  * 2
                  becomes [[1,4,66], [2,4,88], [3,4,66], [4,4,88]].
            """

            new = []
            add = 0
            step = (gbl.BperQ * gbl.QperBar)/fact

            for n in range(fact):
                orig = copy.deepcopy(oldpat)
                for z in orig:
                    z.offset = (z.offset / fact) + add
                    z.duration /= fact
                    if z.duration < 1:
                        z.duration = 1

                    new.append(z)
                add += step

            return tuple( new )


        def shiftPatRiff(oldpat, fact):

            fact = stof(fact, "The shift arg must be a value, not '%s'" % fact)

            # Adjust all the beat offsets

            new = copy.deepcopy(oldpat)
            max = gbl.BperQ * (gbl.QperBar)
            for n in new:
                n.offset += fact * gbl.BperQ
                if n.offset < 0 or n.offset > max:
                    error("Pattern shift with factor %f has resulted in an "
                          "illegal offset" % fact )

            return    tuple( new )

        def patsort(c1, c2):
            """ Sort a pattern tuple. """

            if c1.offset < c2.offset: return -1
            if c1.offset == c2.offset: return 0
            else: return 1


        ### Start of main function...

        # Convert the string to list...
        #  "1 2 3; 4 5 6" --->    [ [1,2,3], [4,5,6] ]

        p = []
        ln = ln.upper().split(';')
        for l in ln:
            p.append(l.split())

        plist=[]


        for ev in p:
            more=[]
            for i,e in enumerate(ev):
                if e.upper() in ('SHIFT', '*'):
                    if i == 0:
                        error("Pattern definition can't start with SHIFT or *")
                    more = ev[i:]
                    ev=ev[:i]
                    break

            if len(ev) == 1:
                nm = (self.vtype, ev[0])

                if nm in pats:
                    if nm[0].startswith('_'):
                        error("You can't use a pattern name beginning with an underscore")
                    pt = pats[nm]

                else:
                    error("%s is not an existing %s pattern"  % (nm[1], nm[0].title()) )

            else:
                pt = [self.getPgroup(ev)]

            while more:
                cmd = more.pop(0)
                if cmd not in ('SHIFT', '*'):
                    error("Expecting SHIFT or *, not '%s'" % cmd)

                if not more:
                    error("Expecting factor after %s" % cmd)
                if cmd == 'SHIFT':
                    pt = shiftPatRiff(pt, more.pop(0))
                elif cmd == '*':
                    pt = mulPatRiff(pt, more.pop(0))

            plist.extend(pt)


        plist.sort(patsort)

        if gbl.swingMode:
            len8  = getNoteLen('8')
            len81 = getNoteLen('81')
            len82 = getNoteLen('82')

            onBeats  = [ x * gbl.BperQ for x in range(gbl.QperBar)]
            offBeats = [ (x * gbl.BperQ + len8) for x in range(gbl.QperBar)]

            for p in plist:
                if p.duration == len8 or self.vtype=="DRUM" and p.duration==1:
                    if p.offset in onBeats:
                        if p.duration == len8:
                            p.duration = len81
                    elif p.offset in offBeats:
                        if p.duration == len8:
                            p.duration = len82
                        i=offBeats.index(p.offset)
                        p.offset = onBeats[i] + len81

        return plist


    def printPattern(self, pat):
        """ Print a pattern. Used by debugging code."""

        s=[]
        for p in pat:
            s.append(" %2.2f %2.0f" % (1+(p.offset/float(gbl.BperQ)),
                p.duration))

            if self.vtype == 'CHORD':
                for a in p.vol:
                    s.append( " %2.0f" % a)

            elif self.vtype == 'BASS':
                f=str(p.noteoffset+1)

                if p.accidental == 1:
                    f+="#"
                elif p.accidental == -1:
                    f+="b"

                if p.addoctave > 0:
                    f+="+" * (p.addoctave/12)
                elif p.addoctave < 0:
                    f+="-" * (p.addoctave/-12)

                s.append( " %s %2.0f" % (f, p.vol ) )

            elif self.vtype == 'ARPEGGIO':
                s.append( " %2.0f " % p.vol )

            elif self.vtype == 'DRUM':
                s.append(" %2.0f" %     p.vol)

            elif self.vtype == 'WALK':
                s.append(" %2.0f" % p.vol )

            s.append(' ;')
            s.append('\n')
        s[-2]='     '
        print "".join(s)


    def insertVoice(self):
        """ Called from bar() and setForceOut(). Adds voice stuff to track."""

        sc = gbl.seqCount

        """ 1st pass for MIDIVOICE. There's a separate slot for
        each bar in the sequence, plus the data can be sent
        before or after 'voice' commands. This first loop
        sends MIDIVOICE data with an offset of 0. Note, we
        don't set the value for 'self.smidiVoice' until we
        do this again, later. All this is needed since some
        MIDIVOICE commands NEED to be sent BEFORE voice selection,
        and others AFTER.
        """

        if self.midiVoice:
            v = self.midiVoice[sc]
            if v and v != self.smidiVoice:
                for i in v:
                    if not i[0]:
                        gbl.mtrks[self.channel].addCtl(gbl.tickOffset, i[1])

        # Set the voice in the midi track if not previously done.

        v=self.voice[sc]
        if v != self.ssvoice:
            gbl.mtrks[self.channel].addProgChange( gbl.tickOffset,    v)
            self.ssvoice = v

            # Mark ssvoice also in shared tracks

            for a in gbl.midiAssigns[self.channel]:
                if gbl.tnames.has_key(a):
                    gbl.tnames[a].ssvoice = v

            if gbl.debug:
                print "Track %s Voice %s inserted" \
                    % (self.name, MMA.midiC.valueToInst(v) )

        """ Our 2nd stab at MIDIVOICE. This time any sequences
            with offsets >0 are sent. AND the smidiVoice and midiSent
            variables are set.
        """

        if self.midiVoice:
            v = self.midiVoice[sc]
            if v and v != self.smidiVoice:
                for i in v:
                    if i[0]:
                        gbl.mtrks[self.channel].addCtl(gbl.tickOffset, i[1])
                self.smidiVoice = v
                self.midiSent = 1  # used by MIDICLEAR


    #########################
    ## Music processing
    #########################


    def bar(self, ctable):
        """ Process a bar of music for this track. """


        # Future vol == de(cresc). Done if track is on or off!

        if self.futureVols:
            self.volume = seqBump([self.futureVols.pop(0)])

        # If track is off don't do anything else.

        if self.disable:
            if self.riff:
                self.riff.pop(0)
            return


        """ Decide which seq to use. This is either the current
            seqCount, or if SeqRnd has been set for the track
            it is a random pattern in the sequence.

            The class variable self.seq is set to the sequence to use.
        """

        if self.seqRnd:
            tmp = []
            for x, i in enumerate(self.seqRndWeight):
                tmp.extend([x] * i)
            if not len(tmp):
                error("SeqRndWeight has generated an empty list")
            self.seq = random.choice(tmp)
        else:
            self.seq = gbl.seqCount

        sc = self.seq

        """ Get pattern for this sequence. Either a Riff or a Pattern. """

        if self.riff:
            pattern = self.riff.pop(0)

        else:
            pattern = self.sequence[sc]

            if not pattern:
                return

        """ MIDI Channel assignment. If no channel is assigned try
            to find an unused number and assign that.
        """

        if not self.channel:
            self.setChannel()

        # We are ready to create musical data. 1st do pending midi commands.

        self.clearPending()

        self.insertVoice()

        # Do MIDISeq for this voice

        if self.midiSeq:
            l = self.midiSeq[sc]
            if l:
                for i in l:
                    gbl.mtrks[self.channel].addCtl( getOffset(i[0]), i[1] )
                self.midiSent = 1

        self.trackBar(pattern, ctable)



    def clearPending(self):

        while self.midiPending:
            c, off, v = self.midiPending.pop(0)
            if c == 'TNAME':
                gbl.mtrks[self.channel].addTrkName(off, v)
                if gbl.debug:
                    print "%s Track name inserted at offset %s" % \
                          (self.name, off)

            elif c == 'GLIS':
                gbl.mtrks[self.channel].addGlis(off, v)
                if gbl.debug:
                    print "%s Glis at offset %s set to %s" % \
                          (self.name, off, ord(chr(v)))

            elif c == 'PAN':
                gbl.mtrks[self.channel].addPan(off, v)
                if gbl.debug:
                    print "%s Pan at offset %s set to %s" % \
                          (self.name, off, v)

            elif c == 'CVOLUME':
                gbl.mtrks[self.channel].addChannelVol(off, v)
                if gbl.debug:
                    print "%s ChannelVolume at offset %s set to %s" % \
                          (self.name, off, v)

            else:
                error("Unknown midi command pending. Call Bob")



    def getChordInPos( self, offset, ctable):
        """ Compare an offset to a list of ctables and return
        the table entry active for the given beat.

        We assume that the first offset in 'ctable' is 0!
        We assme that 'offset' is >= 0!

        Returns a ctable.
        """

        for i in range(len(ctable)-1, -1, -1):    # reverse order
            if offset >= ctable[i].offset:
                break
        return ctable[i]



    def adjustVolume(self, v, beat):
        """ Adjust a note volume based on the track and global volume
            setting.
        """

        if not v:
            return 0

        sc = self.seq

        if self.rSkip[sc] and random.random() < self.rSkip[sc]:
            return 0

        a1 = self.volume[sc]
        if not a1:
            return 0
        a1 *= MMA.volume.vTRatio

        a2 = MMA.volume.volume
        if not a2:
            return 0
        a2 *= MMA.volume.vMRatio

        v *= ( a1 + a2 )

        for b,a in self.accent[sc]:
            if b==beat:
                v += (v * a)

        # take .rVolume % of current volume, add/sub result to current

        if self.rVolume[sc]:
            a = int(v * self.rVolume[sc])
            if a:
                v += random.randrange(-a, a)

        if v > 127:
            v = 127
        elif  v < 1:
            v = 1

        return int(v)


    def adjustNote(self, n):
        """ Adjust a note for a given octave/transposition.
        Ensure that the note is in range.
        """

        n += self.octave[self.seq] + gbl.transpose

        while n < 0:
            n += 12
        while n > 127:
            n -= 12

        while n < self.spanStart:
            n += 12
        while n > self.spanEnd:
            n -= 12

        return n


    def setBarOffset(self, v):
        """ Convert a string into a valid bar offset in midi ticks. """

        m=v.find('-')
        p=v.find('+')

        if m>-1 and p>-1:
            if m>p:
                sp = p
                sign = 1
            else:
                sp = m
                sign = -1

        elif m >- 1:
            sp = m
            sign = -1

        elif p >- 1:
            sp = p
            sign = 1

        else:
            sp = None

        if sp:
            note = v[sp+1:]
            v = v[:sp]
        else:
            note = None


        v=stof(v, "Value for %s bar offset must be integer/float" % self.name)
        v = (v-1) * gbl.BperQ

        if note:
            v += getNoteLen(note) * sign

        if v < 0:
            if v<-gbl.BperQ:
                error("Defining %s Pattern, bar offset must be 0 or greater" %
                  self.name)
            else:
                warning("Offset in '%s' is '%s ticks' before bar start!" % (self.name, -v))

        if v >= gbl.QperBar * gbl.BperQ:
            error("Defining %s Pattern, bar offset must be less than %s" %
                  (self.name, gbl.QperBar + 1))


        return int(v)


    def getDur(self, d):
        """ Return the adjusted duration for a note.

        The adjustment makes notes more staccato. Valid
        adjustments are 1 to 100. 100 is not recommended.
        """

        d = (d * self.artic[self.seq]) / 100
        if not d:
            d = 1

        return d


    def sendNote( self, offset, duration, note, velocity):
        """ Send a note to the MIDI machine. This is called from all
            track classes and handles niceties like mallet-repeat.
        """

        if not velocity:
            return

        sc = self.seq

        rptr = self.mallet

        if rptr and duration > rptr:
            ll = self.getDur(rptr)
            offs = 0
            vel = velocity
            count =0

            for q in range(duration/rptr):
                gbl.mtrks[self.channel].addPairToTrack(
                    offset + offs,
                    self.rTime[sc],
                    ll,
                    note,
                    vel,
                    None )

                offs += rptr
                if self.malletDecay:
                    vel = int( vel + (vel * self.malletDecay) )
                    if vel < 1:
                        vel = 1
                    if vel > 255:
                        vel=255
                count+=1

        else:
            gbl.mtrks[self.channel].addPairToTrack(
                offset,
                self.rTime[sc],
                duration,
                note,
                velocity,
                self.unify[sc] )

