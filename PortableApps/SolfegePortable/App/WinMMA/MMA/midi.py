# midi.py

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
from   MMA.midiM  import intToWord, intTo3Byte, intToLong, intToVarNumber
import MMA.midiC

splitChannels = []

def setSplitChannels(ln):
    """ Parser routine, sets up list of track to split. Overwrites existing. """

    global splitChannels

    splitChannels = []

    for a in ln:
        c = stoi(a)
        if c < 1 or c >16:
            error("SplitChannels: Expecting value 1 to 16, not %s" % c)
        splitChannels.append(c)

    if gbl.debug:
        print "SplitChannels: ",
        printList(splitChannels)


####################

def writeTracks(out):
    """ Write the accumulated MIDI tracks to file. """

    keys=gbl.mtrks.keys()
    keys.sort()

    """ For type 0 MIDI files all data is contained in 1 track.
        We take all our tracks and copy them to track 0, then
        set up keys[] so that only track 0 remains.
    """

    if gbl.midiFileType == 0:
        trk0=gbl.mtrks[0].miditrk
        for n in keys[1:]:
            trk=gbl.mtrks[n].miditrk
            for k,v in trk.items():
                if k in trk0:
                    trk0[k].extend(v)
                else:
                    trk0[k]=v
        keys=[0]

    # Write header

    tcount = len(keys)
    out.write( mkHeader(tcount, gbl.BperQ, gbl.midiFileType) )

    # Write data chunks for each track

    for n in keys:

        if len(gbl.mtrks[n].miditrk):

            if gbl.debug:
                print "Writing <%s> ch=%s;" % \
                    (gbl.mtrks[n].trackname, n),
            
            if n in splitChannels and gbl.midiFileType:
                tcount += writeSplitTrack(n, out)
            else:
                gbl.mtrks[n].writeMidiTrack(out)

    """ We have increased the track count! So, we need to
        fix the file header. This is offset 10/11 which contains
        the number of tracks. The counter tcount has been
        tracking this, so just seek, replace and seek back.
    """

    if tcount != len(keys):
        out.seek(0)
        out.write( mkHeader(tcount, gbl.BperQ, gbl.midiFileType) )
        out.seek(0, 2)  # return to eof


def writeSplitTrack(channel, out):
    """ Split a drum track into a separate track for the non-note
        stuff and then a track for each note.
    """

    tr = gbl.mtrks[channel].miditrk   # track to split

    """ A dict to store the split midi tracks. We'll end out with
        a track for each pitch which appears in the track and
        a track (labeled -1) to store every other than note on data.
    """

    notes={}

    onEvent = 0x90 + (channel-1)
    offEvent = 0x80 + (channel-1)

    for offset in tr.keys():
        for x in range(len(tr[offset])-1, -1, -1):
            ev = tr[offset][x]
            if len(ev) == 3 and ( ord(ev[0]) in (onEvent, offEvent)):
                n = ord(ev[1])
            else:
                n = -1      # special value for non-note on events

            if not notes.has_key(n):   # create a new mtrk if needed
                notes[n]=Mtrk(10)

            if offset in notes[n].miditrk:  # copy event to new track
                notes[n].miditrk[offset].append(ev)
            else:
                notes[n].miditrk[offset]=[ev]

    if gbl.debug:
        print " Data has been split into %s tracks." % len(notes)

    # Insert a channel name in all the new tracks.

    for a in notes.keys():
        if a == -1:
            continue
        if channel == 10:
            m = "%s" % MMA.midiC.valueToDrum(a)
        else:
            m= "%s-%s" % (gbl.mtrks[channel].trackname, a)

        notes[a].addTrkName(0, m)

    for a in sorted(notes.keys()):
        notes[a].writeMidiTrack(out)

    """ The split tracks have been written. Return the number of additional tracks
        so that the caller can properly update the midi file header. Note that
        len(notes)-1 IS CORRECT ... we've already figured on writing 1 track.
    """

    return len(notes)-1


def mkHeader(count, tempo, Mtype):

    return "MThd" + intToLong(6) + intToWord(Mtype) + \
        intToWord(count) + intToWord(tempo)


""" Midi track class. All the midi creation is done here.
    We create a class instance for each track. mtrks{}.
"""

class Mtrk:

    def __init__(self, channel):
        self.miditrk={}
        self.channel = channel-1
        self.trackname = ''
        self.lastEvent = [None] * 129


    def delDup(self, offset, cmd):
        """Delete a duplicate event. Used by timesig, etc.    """

        tr=self.miditrk
        lg=len(cmd)
        if tr.has_key(offset):
            for i,a in enumerate(tr[offset]):
                if a[0:lg] == cmd:
                    del tr[offset][i]


    def addTimeSig(self, offset,  nn, dd, cc, bb):
        """ Create a midi time signature.

            delta - midi delta offset
            nn = sig numerator, beats per measure
            dd - sig denominator, 2=quarter note, 3=eighth,
            cc - midi clocks/tick
            bb - # of 32nd notes in quarter (normally 8)

            This is only called by timeSig.set(). Don't
            call this directly since the timeSig.set() checks for
            duplicate settings.
        """

        cmd = chr(0xff) + chr(0x58)
        self.delDup(offset, cmd)   # NEEDED???
        self.addToTrack(offset, cmd + chr(0x04) + \
            chr(nn) + chr(dd) + chr(cc) + chr(bb) )


    def addKeySig(self, offset, n, mi):
        """ Set the midi key signature. """

        cmd = chr(0xff) + chr(0x59)
        self.delDup(offset, cmd)
        self.addToTrack(offset, cmd + chr(0x02) + chr(n) + chr(mi) )

    def addMarker(self, offset, msg):
        """ Create a midi MARKER event."""

        self.addToTrack(offset, chr(0xff) + chr(0x06) + intToVarNumber(len(msg)) + msg )

    def addText(self, offset, msg):
        """ Create a midi TextEvent."""

        self.addToTrack( offset, chr(0xff) + chr(0x01) + intToVarNumber(len(msg)) + msg )


    def addLyric(self, offset, msg):
        """ Create a midi lyric event. """

        self.addToTrack( offset,
            chr(0xff) + chr(0x05) + intToVarNumber(len(msg)) + msg )


    def addTrkName(self, offset, msg):
        """ Creates a midi track name event. """

        offset = 0 # ignore user offset, always put this at 0

        self.trackname    = msg

        cmd = chr(0xff) + chr(0x03)
        self.delDup(offset, cmd)
        self.addToTrack(offset, cmd + intToVarNumber(len(msg)) + msg )


    def addProgChange( self, offset, program):
        """ Create a midi program change.

            program - midi program

            Returns - packed string
        """

        self.addToTrack(offset,
            chr(0xc0 | self.channel) + chr(program) )


    def addGlis(self, offset, v):
        """ Set the portamento. LowLevel MIDI.

            This does 2 things:
                1. turns portamento on/off,
                2. sets the LSN rate.
        """

        if v == 0:
            self.addToTrack(offset,
                chr(0xb0 | self.channel) + chr(0x41) + chr(0x00) )

        else:
            self.addToTrack(offset,
                chr(0xb0 | self.channel) + chr(0x41) + chr(0x7f) )
            self.addToTrack(offset,
                chr(0xb0 | self.channel) + chr(0x05) + chr(v) )



    def addPan(self, offset, v):
        """ Set the lsb of the pan setting."""

        self.addToTrack(offset,
            chr(0xb0 | self.channel) + chr(0x0a) + chr(v) )


    def addCtl(self, offset, l):
        """ Add arbitary control sequence to track."""

        self.addToTrack(offset, chr(0xb0 | self.channel) + l)


    def addNoteOff(self, offset):
        """ Insert a "All Note Off" into the midi stream.

            Called from the cutTrack() function.
        """

        self.addToTrack(offset,
            chr(0xb0 | self.channel) + chr(0x7b) + chr(0) )


    def addChannelVol(self, offset, v):
        """ Set the midi channel volume."""

        self.addToTrack(offset,
            chr(0xb0 | self.channel) + chr(0x07) + chr(v) )


    def addTempo(self, offset, beats):
        """ Create a midi tempo meta event.

        beats - beats per second

        Return - packed midi string
        """

        cmd = chr(0xff) + chr(0x51)
        self.delDup(offset, cmd)
        self.addToTrack( offset, cmd + chr(0x03) + intTo3Byte(60000000/beats) )


    def writeMidiTrack(self, out):
        """ Create/write the MIDI track.

        We convert timing offsets to midi-deltas.
        """

        tr=self.miditrk

        """ To every MIDI track we generate we add (if the -0 flag
            was set) an on/off beep at offset 0. This makes for
            easier sync in multi-tracks.
        """

        if gbl.synctick and self.channel >= 0:
            self.addToTrack(0, chr(0x90 | self.channel) + chr(80) + chr(90) )
            self.addToTrack(1, chr(0x90 | self.channel) + chr(80) + chr(0) ) 
                        
            
        if gbl.debug:
            ttl = 0
            lg=1
            for t in tr:
                a=len(tr[t])
                if a > lg:
                    lg = a
                ttl += a
            print "Unique ts: %s; Ttl events %s; Average ev/ts %.2f" % \
                (len(tr), ttl,    float(ttl)/len(tr) )

        last = 0

        # Convert all events to MIDI deltas and store in
        # the track array/list

        tdata=[]        # empty track container
        lastSts=None    # Running status tracker

        for a in sorted(tr.keys()):
            delta = a-last
            for d in tr[a]:

                """ Running status check. For each packet compare
                the first byte with the first byte of the previous
                packet. If it is can be converted to running status
                we strip out byte 0. Note that valid running status
                byte are 0x80..0xef. 0xfx are system messages
                and are note suitable for running status.
                """

                if len(d) > 1:
                    if d[0] == lastSts:
                        d=d[1:]
                    else:
                        lastSts = d[0]
                        s=ord(lastSts)
                        if s < 0x80 or s > 0xef or not gbl.runningStatus:
                            lastSts = None

                tdata.extend( [ intToVarNumber(delta) , d ] )
                delta = 0
            last = a

        # Add an EOF to the track (included in total track size)

        tdata.append( intToVarNumber(0))
        tdata.append( chr(0xff) + chr(0x2f) + chr(0x00) )

        tdata = ''.join(tdata)
        totsize = len(tdata)

        out.write("MTrk")
        out.write(intToLong(totsize))
        out.write( tdata )


    def addPairToTrack(self, boffset, startRnd, duration, note, v, unify):
        """ Add a note on/off pair to a track.

        boffset      - offset into current bar
        startRnd  - rand val start adjustment
        duration  - note len
        note      - midi value of note
        v      - midi velocity
        unify      - if set attempt to unify/compress on/offs

        This function tries its best to handle overlapping events.
        Easy to show effect with a table of note ON/OFF pairs. Both
        events are for the same note pitch.

        Offsets     |     200  |      300  |  320  |  420
        ---------|--------|--------|-------|--------
        Pair1     |     on      |       |  off  |
        Pair2     |      |      on   |       |  off

        The logic here will delete the OFF event at 320 and
        insert a new OFF at 300. Result is that when playing
        Pair1 will turn off at 300 followed by the same note
        in Pair2 beginning sounded right after. Why the on/off?
        Remember: Velocities may be different!

        However, if the unify flag is set we should end up with:

        Offsets     |     200  |      300  |  320  |  420
        ---------|--------|--------|-------|--------
        Pair1     |     on      |       |       |
        Pair2     |      |       |       |  off


        """

        # Start/end offsets

        onOffset  = getOffset( boffset, startRnd)
        offOffset = onOffset + duration

        # ON/OFF events

        onEvent     = chr(0x90 | self.channel) + chr(note) + chr(v)
        offEvent = onEvent[:-1] + chr(0)

        """ Check for overlap on last event set for this track and
        do some ugly trickry.

        - The noOnFlag is set if we don't want to have the main
        routine add in the ON event. This is set when UNIFY is
        set and we have an overlap.

        - We set F to the stored event time for this note and,
        if it's in the same event range as the current event
        we loop though the saved events for this track. We are
        looking for a NOTE OFF event.

        - If we get a matching event we then delete it from the
        track. This requires 2 statements: one for an event
        list with only 1 event, a 2nd for multiple events.

        - If UNIFY is NOT set we insert a NOTE OFF at the current
        on time. This replaces the OFF we just deleted.

        - If UNIFY is SET we skip the above step, and we set the
        noOnFlag so that the ON event isn't set.

        """

        noOnFlag = None

        f=self.lastEvent[note]
        if f >= onOffset and f <= offOffset:
            tr=self.miditrk
            for i in range(len(tr[f])):
                if tr[f][i] == offEvent:
                    if len(tr[f]) == 1:
                        del(tr[f])
                    else:
                        del(tr[f][i])
                    if not unify:
                        self.addToTrack(onOffset, offEvent)
                    else:
                        noOnFlag=1
                    break

        if not noOnFlag:
            self.addToTrack(onOffset, onEvent )
        self.addToTrack(offOffset, offEvent )

        # Save the NOTE OFF time for the next loop.

        self.lastEvent[note] = offOffset


    def zapRangeTrack(self, start, end):
        """ Clear NoteOn events from track in range: start ... end.

        This is called from the fermata function.

        We delete the entire event list (3 bytes) from the buffer. This
        can result in empty directory enteries, but that isn't a problem.
        """

        trk=self.miditrk
        for a in trk:
            if a>=start and a<=end:
                for i in range(len(trk[a])-1, -1, -1):
                    e = trk[a][i]
                    if len(e)==3 and ord(e[0]) & 0xF0 == 0x90 and ord(e[2]):
                        del trk[a][i]


    def addToTrack(self, offset, event):
        """ Add an event to a track.

        MIDI data is saved as created in track structures.
        Each track has a miditrk dictionary entry which used
        the time offsets and keys and has the various events
        as data. Each event is packed string of bytes and
        the events are stored as a list in the order they are
        created. Our storage looks like:

        miditrk[123] = [event1, event2, ...]
        """

        if offset<0:
            offset=0

        tr=self.miditrk

        if offset in tr:
            tr[offset].append(event)
        else:
            tr[offset]=[event]




class TimeSig:
    """ Track and set the current time signature.

        Timesigs are completely optional and are inserted into
        the MIDI file by addTimeSig(). MMA routines ignore timesig
        settings.
    """

    def __init__(self):
        """ Initialze to null value, user will never set to this."""

        self.lastsig = (None,None)

    def set(self, nn, dd):
        """ Set timesig. If no change from last value, ignore. """

        if self.lastsig != (nn, dd):
            gbl.mtrks[0].addTimeSig(gbl.tickOffset, nn, dd, 48, 8)
            self.lastsig = (nn, dd)

    def get(self):
        """ Return existing timesig. """

        return self.lastsig


timeSig = TimeSig()



