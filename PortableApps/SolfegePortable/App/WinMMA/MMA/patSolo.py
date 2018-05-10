
# patSolo.py

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

import gbl
from   MMA.common import *
from   MMA.notelen import getNoteLen
import MMA.translate
from   MMA.harmony import harmonize
from   MMA.pat import PC
import MMA.alloc
import MMA.volume


class NoteList:
    def __init__(self, length):
        self.dur = length
        self.velocity = []
        self.nl = []


##############################

class Melody(PC):
    """ The melody and solo tracks are identical, expect that
        the solo tracks DO NOT get saved in grooves and are only
        initialized once.
    """

    vtype = 'MELODY'
    drumType = None
    
    endTilde = []
    drumTone = 38

    def setDrumType(self):
        """ Set this track to be a drum track. """

        if self.channel:
            error("You cannot change a track to DRUM once it has been used")

        self.drumType = 1
        self.setChannel('10')


    def definePattern(self, name, ln):
        error("Melody/solo patterns cannot be defined")


    def restart(self):
        self.ssvoice = -1

    def setTone(self, ln):
        """ A solo track can have a tone, if it is DRUMTYPE."""

        if not self.drumType:
            error("You must set a Solo track to DrumType before setting Tone")

        if len(ln) > 1:
            error("Only 1 value permitted for Drum Tone in Solo tracks")

        self.drumTone = MMA.translate.dtable.get(ln[0])


    def getLine(self, pat, ctable):
        """ Extract a melodyline for solo/melody tracks.

            This is only called from trackbar(), but it's nicer
            to isolate it here.


            RETURNS: notes structure. This is a dictionary. Each key represents
                     an offset in MIDI ticks in the current bar. The data for
                     each entry is an array of notes, a duration and velocity:

                     notes[offset].dur         - duration in ticks
                     notes[offset].velocity[]  - velocity for notes
                     notes[offset].defaultVel  - default velocity for this offset
                     notes[offset].nl[]        - list of notes (if the only note value
                                                 is None this is a rest placeholder)

        """

        sc = self.seq
        barEnd = gbl.BperQ*gbl.QperBar

        acc=keySig.getAcc()

        # list of notename to midivalues

        midiNotes = {'c':0, 'd':2, 'e':4, 'f':5, 'g':7, 'a':9, 'b':11, 'r':None }

        """ The initial string is in the format "1ab;4c;;4r;". The trailing
            ';' is important and needed. If we don't have this requirement
            we can't tell if the last note is a repeat of the previous. For
            example, if we have coded "2a;2a;" as "2a;;" and we didn't
            have the 'must end with ;' rule, we end up with "2a;" and
            then we make this into 2 notes...or do we? Easiest just to
            insist that all bars end with a ";".
        """

        if not pat.endswith(';'):
            error("All Solo strings must end with a ';'")

        """ Take our list of note/value pairs and decode into
            a list of midi values. Quite ugly.
        """

        if gbl.swingMode:
            len8 = getNoteLen('8')
            len81 = getNoteLen('81')
            len82 = getNoteLen('82')
            onBeats = [ x * gbl.BperQ for x in range(gbl.QperBar)]
            offBeats = [ (x * gbl.BperQ + len8) for x in range(gbl.QperBar)]


        length = getNoteLen('4')    # default note length
        lastc = ''                  # last parsed note
        velocity = 90               # intial/default velocity for solo notes

        notes={}   # A dict of NoteList, keys == offset

        if self.drumType:
            isdrum = 1
            lastc = str(self.drumTone)
        else:
            isdrum = None

        pat = pat.replace(' ', '').split(';')[:-1]

        # set initial offset into bar

        if pat[0].startswith("~"):
            pat[0]=pat[0][1:]
            if not self.endTilde or self.endTilde[1] != gbl.tickOffset:
                error("Previous line did not end with '~'")
            else:
                offset = self.endTilde[0]
        else:
            offset = 0
        lastOffset = None

        # Strip off trailing ~

        if pat[-1].endswith("~"):
            self.endTilde = [1, gbl.tickOffset + (gbl.BperQ * gbl.QperBar) ]
            pat[-1]=pat[-1][:-1]
        else:
            self.endTilde = []


        # Begin parse loop

        for a in pat:
            if a == '<>':
                continue

            if offset >= barEnd:
                error("Attempt to start Solo note '%s' after end of bar" % a)

            # strip out all '<volume>' setting and adjust velocity

            a, vls = pextract(a, "<", ">")
            if vls:
                if len(vls) > 1:
                    error("Only 1 volume string is permitted per note-set")

                vls = vls[0].upper().strip()
                if not vls in MMA.volume.vols:
                    error("%s string Expecting a valid volume, not '%s'" % \
                        (self.name, vls))
                velocity *= MMA.volume.vols[vls]


            """ Split the chord chunk into a note length and notes. Each
                part of this is optional and defaults to the previously
                parsed value.
            """

            i = 0
            while i < len(a):
                if not a[i] in '1234568.+':
                    break
                else:
                    i+=1

            if i:
                l=getNoteLen(a[0:i])
                c=a[i:]
            else:
                l=length
                c=a

            if not c:
                c=lastc
                if not c:
                    error("You must specify the first note in a solo line")

            length = l    # set defaults for next loop
            lastc = c


            """ Convert the note part into a series of midi values
                Notes can be a single note, or a series of notes. And
                each note can be a letter a-g (or r), a '#,&,n' plus
                a series of '+'s or '-'s. Drum solos must have each
                note separated by ','s: "Snare1,Kick1,44".
            """

            if isdrum:
                c=c.split(',')
            else:
                c=list(c)

            while c:

                # Parse off note name or 'r' for a rest

                name = c.pop(0)

                if name == 'r' and (offset in notes or c):
                    error("You cannot combine a rest with a note in a chord for solos")


                if not isdrum:
                    if not name in midiNotes:
                        error("%s encountered illegal note name '%s'"
                            % (self.name, name))

                    v = midiNotes[ name ]

                    # Parse out a "#', '&' or 'n' accidental.

                    if c and c[0]=='#':
                        c.pop(0)
                        acc[name] = 1

                    elif c and c[0]=='&':
                        c.pop(0)
                        acc[name] = -1

                    elif c and c[0]=='n':
                        c.pop(0)
                        acc[name] = 0

                    if v != None:
                        v += acc[name]

                    # Parse out +/- (or series) for octave

                    if c and c[0] == '+':
                        while c and c[0] == '+':
                            c.pop(0)
                            v += 12
                    elif c and c[0] == '-':
                        while c and c[0] == '-':
                            c.pop(0)
                            v -= 12

                else:
                    if not name:        # just for leading '.'s
                        continue
                    if name == 'r':
                        v = midiNotes[ name ]
                    elif name == '*':
                        v = self.drumTone
                    else:
                        v = MMA.translate.dtable.get(name)


                """ Swingmode -- This tests for successive 8ths on/off beat
                If found, the first is converted to 'long' 8th, the 2nd to a 'short'
                and the offset for the 2nd is adjusted to comp. for the 'long'.
                """

                if gbl.swingMode and l==len8 and \
                       offset in offBeats and \
                       lastOffset in onBeats and \
                       lastOffset in notes:
                    if notes[lastOffset].dur == len8:
                        offset = lastOffset + len81
                        notes[lastOffset].dur = len81
                        l=len82


                   # create a new note[] entry for this offset

                if not offset in notes:
                    notes[offset] = NoteList(l)

                # add note event to note[] array

                notes[offset].nl.append(v)
                notes[offset].velocity.append(self.adjustVolume(velocity, offset))

                notes[offset].defaultVel = velocity   # needed for addHarmony()

            lastOffset = offset
            offset += l


        if offset <= barEnd:
            if self.endTilde:
                error("Tilde at end of bar has no effect")

        else:
            if self.endTilde:
                self.endTilde[0]=offset-barEnd
            else:
                warning("%s, end of last note overlaps end of bar by %2.3f "
                    "beat(s)." % (self.name, (offset-barEnd)/float(gbl.BperQ)))

        return notes


    def addHarmony(self, notes, ctable):
        """ Add harmony to solo notes. """

        sc=self.seq

        harmony = self.harmony[sc]
        harmOnly = self.harmonyOnly[sc]
        
        
        for offset in notes:
            nn = notes[offset]
            
            if len(nn.nl) == 1 and nn.nl[0] != None:
                tb = self.getChordInPos(offset, ctable)
                
                if tb.chordZ:
                    continue

                h = harmonize(harmony, nn.nl[0], tb.chord.bnoteList)

                """ If harmonyonly set then drop note, substitute harmony,
                    else append harmony notes to chord.
                """
                
                if harmOnly:
                    nn.nl = h
                    nn.velocity = []
                    off=0
                else:
                    nn.nl.extend(h)
                    off=1

                # Create velocites for harmony note(s)

                for i in range(off,len(nn.nl)):
                    nn.velocity.append(self.adjustVolume(nn.defaultVel *
                          self.harmonyVolume[sc], offset))

        return notes



    def trackBar(self, pat, ctable):
        """ Do the solo/melody line. Called from self.bar() """

        notes = self.getLine(pat, ctable)

        if self.harmony[self.seq] and not self.drumType:
            self.addHarmony(notes, ctable)

        sc=self.seq
        unify = self.unify[sc]

        rptr = self.mallet

        for offset in sorted(notes.keys()):
            nn=notes[offset]

            for n,v  in zip(nn.nl, nn.velocity):
                if n == None:     # skip rests
                    continue

                if not self.drumType:        # octave, transpose
                    n = self.adjustNote(n)

                self.sendNote( offset, self.getDur(nn.dur), n, v)



class Solo(Melody):
    """ Pattern class for a solo track. """

    vtype = 'SOLO'


    # Grooves are not saved/restored for solo tracks.

    def restoreGroove(self, gname):
        self.setSeqSize()

    def saveGroove(self, gname):
        pass


##################################

""" Keysignature. This is only used in the solo/melody tracks so it
    probably makes sense to have the parse routine here as well. To
    contain everything in one location we make a single instance class
    of the whole mess.
"""

class KeySig:

    def __init__(self):
        self.kSig = 0

    majKy = { "C" :  0, "G" :  1, "D" :  2,
              "A" :  3, "E" :  4, "B" :  5,
              "F#":  6, "C#":  7, "F" : -1,
              "Bb": -2, "Eb": -3, "Ab": -4,
              "Db": -5, "Gb": -6, "Cb": -7 }

    minKy = { "A" :  0, "E" :  1, "B" :  2,
              "F#":  3, "C#":  4, "G#":  5,
              "D#":  6, "A#":  7, "D" : -1,
              "G" : -2, "C" : -3, "F" : -4,
              "Bb": -5, "Eb": -6, "Ab": -7 }

    def set(self,ln):
        """ Set the keysignature. Used by solo tracks."""

        mi = 0

        if len(ln) < 1 or len(ln) > 2:
            error("KeySig only takes 1 or 2 arguments")

        if len(ln) == 2:
            l=ln[1][0:3].upper()
            if l == 'MIN':
                mi=1
            elif l == 'MAJ':
                mi=0
            else:
                error("KeySig 2nd arg must be 'Major' or 'Minor', not '%s'" % ln[1])

        l=ln[0]

        t=l[0].upper() + l[1:]

        if mi and t in self.minKy:
            self.kSig = self.minKy[t]
        elif not mi and t in self.majKy:
                self.kSig = self.majKy[t]
        elif l[0] in "ABCDEFG":
            error("There is no key signature name: '%s'" % l)

        else:
            c=l[0]
            f=l[1].upper()

            if not f in ("B", "&", "#"):
                error("2nd char in KeySig must be 'b' or '#', not '%s'" % f)

            if not c in "01234567":
                error("1st char in KeySig must be digit 0..7,  not '%s'" % c)

            self.kSig = int(c)

            if f in ('B', '&'):
                self.kSig = -self.kSig


            if not c in "01234567":
                error("1st char in KeySig must be digit 0..7,  not '%s'" % c)


        # Set the midi meta track with the keysig. This doen't do anything
        # in the playback, but other programs may use it.

        n = self.kSig
        if n < 0:
            n = 256 + n

        gbl.mtrks[0].addKeySig(gbl.tickOffset, n, mi)

        if gbl.debug:
            n = self.kSig
            if n >= 0:
                f = "Sharps"
            else:
                f = "Flats"

            print "KeySig set to %s %s" % (abs(n), f)


    def getAcc(self):
        """ The solo parser needs to know which notes are accidentals.
            This is simple with a keysig table. There is an entry for each note,
            either -1,0,1 corresponding to flat,natural,sharp. We populate
            the table for each bar from the keysig value. As we process
            the bar data we update the table. There is one flaw here---in
            real music an accidental for a note in a give octave does not
            effect the following same-named notes in different octaves.
            In this routine IT DOES.

            NOTE: This is recreated for each bar of music for each solo/melody track.
        """

        acc = {'a':0, 'b':0, 'c':0, 'd':0, 'e':0, 'f':0, 'g':0  }
        ks=self.kSig

        if ks < 0:
            for a in range( abs(ks) ):
                acc[ ['b','e','a','d','g','c','f'][a] ] = -1

        else:
            for a in range(ks):
                acc[ ['f','c','g','d','a','e','b'][a] ] = 1

        return acc


keySig=KeySig()    # single instance


#######################

""" When solos are included in a chord/data line they are
    assigned to the tracks listed in this list. Users can
    change the tracks with the setAutoSolo command.
"""

autoSoloTracks = [ 'SOLO', 'SOLO-1', 'SOLO-2', 'SOLO-3' ]


def setAutoSolo(ln):
    """ Set the order and names of tracks to use when assigning
        automatic solos (specified on chord lines in {}s).
    """

    global autoSoloTracks

    if not len(ln):
        error("You must specify at least one track for autosolos")

    autoSoloTracks = []
    for n in ln:
        n=n.upper()
        MMA.alloc.trackAlloc(n, 1)
        if gbl.tnames[n].vtype not in ('MELODY', 'SOLO'):
            error("All autotracks must be Melody or Solo tracks, not %s" % gbl.tnames[n].vtype)

        autoSoloTracks.append(n)

    if gbl.debug:
        print "AutoSolo track names:",
        for a in autoSoloTracks:
            print a,
        print



###############


def extractSolo(ln, rptcount):
    """ Parser calls this to extract solo strings. """

    a = ln.count('{')
    b = ln.count('}')

    if a != b:
        error("Mismatched {}s for solo found in chord line")

    if a:
        if rptcount > 1:
            error("Bars with both repeat count and solos are not permitted")

        ln, solo = pextract(ln, '{', '}')

        if len(solo) > len(autoSoloTracks):
            error("Too many melody/solo riffs in chord line. %s used, "
                  "only %s defined" % (len(solo), len(autoSoloTracks)) )


        firstSolo = solo[0][:]  # save for autoharmony tracks

        """ We have the solo information. Now we loop though each "solo" and:
              1. Ensure or Create a MMA track for the solo
              2. Push the solo data into a Riff for the given track.
        """

        for s, trk in zip(solo, autoSoloTracks):
            MMA.alloc.trackAlloc(trk, 1)
            gbl.tnames[trk].setRiff( s.strip() )


        """ After all the solo data is interpreted and sent to the
            correct track, we check any leftover tracks. If any of these
            tracks are  empty of data AND are harmonyonly the note
            data from the first track is interpeted again for that
            track. Tricky: the max() is needed since harmonyonly can
            have different setting for each bar...this way
            the copy is done if ANY bar in the seq has harmonyonly set.
        """

        for t in autoSoloTracks[1:]:
            if gbl.tnames.has_key(t) and gbl.tnames[t].riff == [] \
                   and max(gbl.tnames[t].harmonyOnly):
                gbl.tnames[t].setRiff( firstSolo[:] )

            if gbl.debug:
                print "%s duplicated to %s for HarmonyOnly." % (trk, t)

    return ln

