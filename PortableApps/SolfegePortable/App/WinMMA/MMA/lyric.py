
# lyric.py

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


class Lyric:

    textev    = None    # set if TEXT EVENTS (not recommended)
    barsplit  = None    # set if lyrics NOT split into sep. events for bar
    versenum  = 1       # current verse number of lyric
    dupchords = 0       # set if we want chords as lyric events
    transpose = 0       # tranpose chord names (for dupchords only)

    pushedLyrics = []

    transNames = ( ('C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'),
                   ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'))

    transKey = 0   #  0==flat, 1=sharp

    chordnames={
        'B#': 0, 'C' : 0, 'C#': 1, 'Db': 1,
        'D' : 2, 'D#': 3, 'Eb': 3, 'E' : 4,
        'Fb': 4, 'E#': 5, 'F' : 5, 'F#': 6,
        'Gb': 6, 'G' : 7, 'G#': 8, 'Ab': 8,
        'A' : 9, 'A#': 10,'Bb': 10,'B' : 11,
        'Cb':11 }


    def __init__(self):
        pass


    def setting(self):
        """ Called from macro. """

        a="Event="

        if self.textev: a+="Text"
        else:           a+="Lyric"

        a+=" Split="
        if self.barsplit: a+="Bar"
        else:             a+="Normal"

        a += " Verse=%s" % self.versenum

        a += " Chords="
        if self.dupchords: a+="On"
        else:              a+="Off"

        a += " Transpose=%s" % self.transpose

        a += " CNames="
        if self.transKey:  a+="Sharp"
        else:              a+="Flat"

        return a


    def option(self, ln):
        """ Set a lyric option. """

        for i, l in enumerate(ln):
            l=l.upper()

            # Single word options

            if l.upper()=="SET":

                if i>=len(ln):
                    s=''
                else:
                    s=' '.join(ln[i+1:]).strip()

                if not s.startswith('['):
                    s = '[' + s + ']'

                self.pushedLyrics.append(s)

                break


            # All the rest are OPT=VALUE pairs

            try:
                a,v = l.split('=')
            except:
                error("Lyric options must be in CMD=VALUE pairs")


            if a == 'EVENT':
                if v == 'TEXT':
                    self.textev = 1
                    warning ("Lyric: Placing lyrics as TEXT EVENTS  is not recommended")

                elif v == 'LYRIC':
                    self.textev = None
                    if gbl.debug:
                        print "Lyric: lyrics set as LYRIC events."

                else:
                    error("Valid options for Lyric Event are TEXT or LYRIC")


            elif a == 'SPLIT':
                if v == 'BAR':
                    self.barsplit = 1
                    if gbl.debug:
                        print "Lyric: lyrics distributed thoughout bar."

                elif v == 'NORMAL':
                    self.barsplit = None
                    if gbl.debug:
                        print "Lyric: lyrics appear as one per bar."

                else:
                    error("Valid options for Lyric Split are BAR or NORMAL")


            elif a == 'VERSE':
                if v.isdigit():
                    self.versenum = int(v)

                elif v == 'INC':
                    self.versenum += 1

                elif v == 'DEC':
                    self.versenum -= 1

                else:
                    error("Valid options of Lyric Verse are <nn> or INC or DEC")

                if self.versenum < 1:
                    error("Attempt to set Lyric Verse to %s. Values "
                        "must be > 0" % self.versenum)

                if gbl.debug:
                    print "Lyric: verse number set to %s" % self.versenum


            elif a == 'CHORDS':
                if v in ('1', 'ON'):
                    self.dupchords = 1
                    if gbl.debug:
                        print "Lyric: chords are duplicated as lyrics."

                elif v in ('0', 'OFF'):
                    self.dupchords = 0
                    if gbl.debug:
                        print "Lyric: chords are NOT duplicated as lyrics."

                else:
                    error ("Expecting 'ON' or 'OFF' in Lyric directive, not 'CHORDS=%s'" % v)

            elif a == 'TRANSPOSE':

                v = stoi(v, "Lyric Tranpose expecting value, not %s" % v)

                if v < -12 or v > 12:
                    error("Lyric Tranpose %s out-of-range; must be -12..12" % v)

                self.transpose = v

            elif a == 'CNAMES':

                if v in ('#', 'SHARP'):
                    self.transKey = 1
                elif v in ('B', '&', 'FLAT'):
                    self.transKey = 0

                else:
                    error("Lyric CNames expecting 'Sharp' or 'Flat', not '%s'" % v )

            else:
                error("Usage: Lyric expecting EVENT, SPLIT, VERSE, CHORDS, TRANSPOSE, CNAMES or SET, "
                    "not '%s'" % a )





    def leftovers(self):
        """ Just report leftovers on stack."""

        if self.pushedLyrics:
            warning("Lyrics remaining on stack")


    def extract(self, ln, rpt):
        """ Extract lyric info from a chord line and place in META track.

            Returns line and lyric as 2 strings.

            The lyric is returned for debugging purposes, but it has been
            processed and inserted into the MIDI track.
        """

        a=ln.count('[')
        b=ln.count(']')

        if a != b:
            error("Mismatched []s for lyrics found in chord line")

        if self.pushedLyrics:
            if a or b:
                error("Lyrics not permitted inline and as LYRIC SET")


            ln = ln + self.pushedLyrics.pop(0)
            a=b=1      # flag that we have lyrics, count really doesn't matter


        if rpt > 1:
            if self.dupchords:
                error("Chord to lyrics not supported with bar repeat")
            elif a or b:
                error("Bars with both repeat count and lyrics are not permitted")


        ln, lyrics = pextract(ln, '[', ']')


        """ If the CHORDS=ON option is set, make a copy of the chords and
            insert as lyric. This permits illegal chord lines, but they will
            be caught by the parser.
        """

        if self.dupchords:
            ly = []

            for v in ln.split():
                v = v.replace('&', 'b')
                if v == 'z':
                    v = 'N.C.'
                if 'z' in v:
                    v = v.split('z')[0]
                while v.startswith('-'):
                    v=v[1:]
                while v.startswith('+'):
                    v=v[1:]

                if self.transpose:
                    tr=0   # Needed in case line is invalid!
                    cn=v[0:2]
                    if self.chordnames.has_key(cn):
                        tr=self.chordnames[cn] + self.transpose

                    else:
                        cn=v[0:1]
                        if self.chordnames.has_key(cn):
                            tr=self.chordnames[cn] + self.transpose

                    while tr>=12: tr-=12
                    while tr<=-12: tr+=12

                    if tr:
                        v = self.transNames[self.transKey][tr] + v[len(cn):]


                ly.append(v)

            i=gbl.QperBar - len(ly)
            if i>0:
                ly.extend( ['/'] * i )
            lyrics.insert(0, ' '.join(ly) + '\\r')


        v=self.versenum

        if len(lyrics) == 1:
            v=1

        if v > len(lyrics):
            lyrics = ''
        else:
            lyrics=lyrics[v-1]

        if not len(lyrics):
            return (ln, [])

        lyrics=lyrics.replace('\\r', ' \\r ')
        lyrics=lyrics.replace('\\n', ' \\n ')
        lyrics=lyrics.replace('     ', ' ')

        if self.barsplit:
            lyrics = [lyrics]
        else:
            lyrics = lyrics.split()

        beat = 0
        bstep = gbl.QperBar / float(len(lyrics))


        for t, a in enumerate(lyrics):
            a,b = pextract(a, '<', '>', 1)

            if b and b[0]:
                beat = stof(b[0], "Expecting value in <%s> in lyric" % b)
                if beat < 1     or beat > gbl.QperBar+1:
                    error("Offset in lyric <> must be 1 to %s" % gbl.QperBar)
                beat -= 1
                bstep = (gbl.QperBar-beat)/float((len(lyrics)-t))

            a = a.replace('\\r', '\r')
            a = a.replace('\\n', '\n')

            if a and a != ' ':
                if not a.endswith('-'):
                    a += ' '

                p=getOffset(beat * gbl.BperQ)
                if self.textev:
                    gbl.mtrks[0].addText(p, a)
                else:
                    gbl.mtrks[0].addLyric(p, a)

            beat += bstep

        return (ln, lyrics)


# Create a single instance of the Lyric Class.

lyric = Lyric()

