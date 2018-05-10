
# parse.py

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


This module does all file parsing. Most commands
are passed to the track classes; however, things
like TIME, SEQRND, etc. which just set global flags
are completely handled here.

"""

import os
import random
import copy

import gbl
import MMA.notelen
import MMA.chords
import MMA.file
import MMA.docs
import MMA.midi
import MMA.midiIn
import MMA.auto
from   MMA.alloc import trackAlloc
from   MMA.common import *
import MMA.translate
from   MMA.lyric import lyric
import MMA.patSolo
from   MMA.macro import macros
import MMA.mdefine
import MMA.volume
from   MMA.pat import seqBump

lastChord = None   # tracks last chord for "/ /" data lines.

beginData = []      # Current data set by a BEGIN statement
beginPoints = []    # since BEGINs can be nested, we need ptrs for backing out of BEGINs

seqRndWeight = [1]

groovesList = None
groovesCount = 0

gmagic = 9988   # magic name for groove saved with USE

""" This table is passed to the track classes. It has
    an instance for each chord in the current bar.
"""

class CTable:
    chord     = None    # A pointer to the chordNotes structures
    chordZ    = None    # set if chord is tacet
    arpeggioZ = None    # set if arpeggio is tacet
    walkZ     = None    # set if walking bass is tacet
    drumZ     = None    # set if drums are tacet
    bassZ     = None    # set if bass is tacet
    scaleZ    = None    # set if scale track is tacet
    ariaZ     = None    # set if aria track is tacet

    def __init__(self, offset):
        self.offset=offset



########################################
# File processing. Mostly jumps to pats
########################################


def parseFile(n):
    """ Open and process a file. Errors exit. """

    fp=gbl.inpath

    f=MMA.file.ReadFile(n)

    parse(f)
    gbl.inpath=fp

    if gbl.debug:
        print "File '%s' closed." % n


def parse(inpath):
    """ Process a mma input file. """

    global beginData, lastChord
    global groovesList, groovesCount

    gbl.inpath = inpath

    curline = None

    while 1:
        curline = inpath.read()

        if curline == None:
            MMA.docs.docDump()
            break

        l = macros.expand(curline)

        """ Handle BEGIN and END here. This is outside of the Repeat/End
            and variable expand loops so SHOULD be pretty bullet proof.
            Note that the beginData stuff is global to this module ... the
            Include/Use directives check to make sure we're not doing that
            inside a Begin/End.

            beginData[] is a list which we append to as more Begins are
            encountered.

            The placement here is pretty deliberate. Variable expand comes
            later so you can't macorize BEGIN ... I think this makes sense.
        """

        key=l[0].upper()
        if key == 'BEGIN':
            if not l:
                error("Use: Begin STUFF")
            beginPoints.append(len(beginData))
            beginData.extend(l[1:])
            continue

        if key == 'END':
            if len(l) > 1:
                error("No arguments permitted for END")
            if not beginData:
                error("No 'BEGIN' for 'END'")
            beginData=beginData[:beginPoints.pop(-1)]
            continue

        if beginData:
            l = beginData + l

        action = l[0].upper()

        if gbl.showExpand and action !='REPEAT':
            print l

        # If the command is in the simple function table, jump & loop.

        if action in simpleFuncs:
            simpleFuncs[action](l[1:])
            continue


        """ We have several possibilities ...
            1. The command is a valid assigned track name,
            2. The command is a valid track name, but needs to be
               dynamically allocated,
            3. It's really a chord action
        """

        if not action in gbl.tnames:
            trackAlloc(action, 0)    # ensure that track is allocated

        if action in gbl.tnames:    #  BASS/DRUM/APEGGIO/CHORD

            name = action
            if len(l) < 2:
                error("Expecting argument after '%s'" % name)
            action = l[1].upper()

            if action in trackFuncs:
                trackFuncs[action](name, l[2:])
            else:
                error ("Don't know '%s'" % curline)

            continue

        ### Gotta be a chord data line!


        """ A data line can have an optional bar number at the start
            of the line. Makes debugging input easier. The next
            block strips leading integers off the line. Note that
            a line number on a line by itself it okay.
        """

        if l[0].isdigit():
            l = l[1:]
            if not l:        # ignore empty lines
                continue

        """ A bar can have an optional repeat count. This must
            be at the end of bar in the form '* xx'.
        """

        if len(l)>1 and l[-2]=='*':
            rptcount = stoi(l[-1], "Expecting integer after '*'")
            l=l[:-2]
        else:
            rptcount = 1


        """ Extract solo(s) from line ... this is anything in {}s.
            The solo data is pushed into RIFFs and discarded from
            the current line.
        """

        l = ' '.join(l)
        l = MMA.patSolo.extractSolo(l, rptcount)

        """ Set lyrics from [stuff] in the current line or
            stuff previously stored with LYRICS SET.
        """

        l, lyrics = lyric.extract(l, rptcount)

        """ At this point we have only chord info. A number
            of sanity checks are made:
              1. Make sure there is some chord data,
              2. Ensure the correct number of chords.
        """

        l = l.split()

        if not l:
            error("Expecting music (chord) data. Even lines with\n"
                  "  lyrics or solos still need a chord")

        i = gbl.QperBar - len(l)
        if i<0:
            error("Too many chords in line. Max is %s, not %s" %
                  (gbl.QperBar, len(l) ) )
        if i:
            l.extend( ['/'] * i )


        """ We now have a valid line. It'll look something like:

              ['Cm', '/', 'z', 'F#']

            For each bar we create a ctable structure. This is just
            a list of CTables, one for each beat division.
            Each entry has the offset (in midi ticks), chordname, etc.

            Special processing in needed for 'z' options in chords. A 'z' can
            be of the form 'CHORDzX', 'z!' or just 'z'.
        """

        beat = 0
        ctable = []

        for c in l:
            if c == '/':
                if not lastChord:
                    error("A chord has to be set before you can use a '/'")
                c = lastChord
            else:
                lastChord = c

            ctable.append(parseZs(c, beat))
            beat += 1

        # Create MIDI data for the bar

        for rpt in range(rptcount):
            if MMA.volume.futureVol:
                MMA.volume.volume = MMA.volume.futureVol.pop(0)

            tmp = []
            for x, i in enumerate(seqRndWeight):
                tmp.extend([x] * i)
            if not len(tmp):
                error("SeqRndWeight has generated an empty list")
            randomSeq = random.choice(tmp)

            if gbl.seqRnd[0] == 1:
                gbl.seqCount = randomSeq

            """ Process each track. It is important that the track classes
                are written so that the ctable passed to them IS NOT MODIFIED.
                This applies especially to chords. If the track class changes
                the chord, then restore it before returning!!!
            """

            for a in gbl.tnames.values():
                seqSave = gbl.seqCount
                if a.name in gbl.seqRnd:
                    gbl.seqCount = randomSeq

                a.bar(ctable)    ## process entire bar!

                gbl.seqCount = seqSave

            # Adjust counters

            gbl.barNum += 1

            if gbl.barNum > gbl.maxBars:
                error("Capacity exceeded. Maxbar setting is %s. Use -m option"
                      % gbl.maxBars)

            gbl.tickOffset += (gbl.QperBar * gbl.BperQ)

            gbl.seqCount = (gbl.seqCount+1) % gbl.seqSize

            """ Handle groove lists. If there is more than 1 entry
                in the groove list, advance (circle). We don't have
                to qualify grooves since they were verified when
                this list was created. groovesList==None if there
                is only one groove (or none).
            """

            if groovesList:
                groovesCount += 1
                if groovesCount > len(groovesList)-1:
                    groovesCount = 0
                slot = groovesList[groovesCount]

                if slot !=  gbl.currentGroove:
                    grooveDo(slot)

                    gbl.lastGroove = gbl.currentGroove
                    gbl.currentGroove = slot

                    if gbl.debug:
                        print "Groove (list) setting restored from '%s'." % slot

            # Enabled with the -r command line option

            if gbl.showrun:
                print "%3d:" % gbl.barNum,
                for c in l:
                    print c,
                if lyrics:
                    print lyrics,
                print


def parseZs(c, beat):
    """ Parse a chord in a barline, create Ctable and strips 'z's.

        This is called only from the main parser, but it's
        complicated (ugly) enough to have its own function.
    """

    ctab = CTable(beat * gbl.BperQ)

    if 'z' in c:
        c, r = c.split('z', 1)    # chord name/track mute

        if not c:
            if    r=='!': # mute all for 'z!'
                r='DCAWBSR'
                c='z'        # dummy chord name
            elif not r: # mute all tracks except Drum 'z'
                r='CBAWSR'
                c='z'

            else:
                error("To mute individual tracks you must "
                      "use a chord/z combination not '%s'" % r)

        else:    # illegal construct -- 'Cz!'
            if r=='!':
                error("'%sz!' is illegal. 'z!' mutes all tracks "
                      "so you can't include the chord" % c)

            elif not r:
                error("'%sz' is illegal. You must specify tracks "
                          "if you use a chord" % c )

        for v in r:
            if v == 'C':
                ctab.chordZ = 1
            elif v == 'B':
                ctab.bassZ = 1
            elif v == 'A':
                ctab.arpeggioZ = 1
            elif v == 'W':
                ctab.walkZ = 1
            elif v == 'D':
                ctab.drumZ = 1
            elif v == 'S':
                ctab.scaleZ = 1
            elif v == 'R':
                ctab.ariaZ = 1

            else:
                error("Unknown voice '%s' for rest in '%s'" % (v,r))

    ctab.chord = MMA.chords.ChordNotes(c)

    return ctab

##################################################################

def allTracks(ln):
    """ Apply track to all tracks. """

    allTypes = ('BASS', 'CHORD', 'ARPEGGIO', 'SCALE', 'DRUM', 'WALK', 'MELODY', 'SOLO')
    ttypes = []

    if len(ln) < 1:
        error("AllTracks: argument (track?) required")

    i = 0
    while i < len(ln) and ln[i].upper() in allTypes:
        ttypes.append(ln[i].upper())
        i += 1

    if ttypes == []:
        ttypes = allTypes

    if i>=len(ln):
        error("AllTracks: Additional argument (command?) required")

    cmd = ln[i].upper()
    args = i+1

    if not cmd in trackFuncs:
        error("AllTracks: command '%s' doen't exist" % cmd)

    for n in gbl.tnames:
        if not gbl.tnames[n].vtype in ttypes:
            continue

        trackFuncs[cmd](n, ln[args:])


#######################################
# Do-nothing functions

def comment(ln):
    pass

def repeatend(ln):
    error("Repeatend/EndRepeat without Repeat")

def repeatending(ln):
    error("Repeatending without Repeat")

def endmset(ln):
    error("EndMset/MSetEnd without If")

def ifend(ln):
    error("ENDIF without IF")

def ifelse(ln):
    error("ELSE without IF")



#######################################
# Repeat/jumps


def repeat(ln):
    """ Repeat/RepeatEnd/RepeatEnding.

        Read input until a RepeatEnd is found. The entire
        chunk is pushed back into the input stream the
        correct number of times. This accounts for endings and
        nested repeats.
    """


    def repeatChunk():
        q=[]
        qnum=[]
        nesting = 0

        while 1:
            l=gbl.inpath.read()

            if not l:
                error("EOF encountered processing Repeat")

            act=l[0].upper()

            if act=='REPEAT':
                nesting += 1

            elif act in ('REPEATEND', 'ENDREPEAT') and nesting:
                nesting -= 1

            elif act == 'REPEATENDING' and nesting:
                pass

            elif act in ('REPEATEND', 'ENDREPEAT', 'REPEATENDING'):
                return (q, qnum, act, l[1:])

            q.append(l)
            qnum.append(gbl.lineno)

    stack=[]
    stacknum=[]
    main=[]
    mainnum=[]
    ending = 0

    if ln:
        error("REPEAT takes no arguments")

    main, mainnum, act, l = repeatChunk()

    while 1:
        if act in ('REPEATEND', 'ENDREPEAT'):
            if l:
                l=macros.expand(l)
                if len(l) == 2 and l[0].upper() == 'NOWARN':
                    l=l[1:]
                    warn=0
                else:
                    warn=1

                if len(l) != 1:
                    error("%s: Use [NoWarn] Count" % act)

                count=stoi(l[0], "%s takes an integer arg" % act)

                if count == 2 and warn:
                    warning("%s count of 2 duplicates default. Did you mean 3 or more?" % act)

                elif count == 1 and warn:
                    warning("%s count of 1 means NO REPEAT" % act)

                elif count == 0 and warn:
                    warning("%s count of 0, Skipping entire repeated section" % act)

                elif count < 0:
                    error("%s count must be 0 or greater" % act)

                elif count > 10 and warn:
                    warning("%s is a large value for %s" % (count, act) )

            else:
                count=2

            if not ending:
                count += 1
            for c in range(count-1):
                stack.extend(main)
                stacknum.extend(mainnum)
            gbl.inpath.push(stack, stacknum)
            break

        elif act == 'REPEATENDING':
            ending = 1

            if l:
                l=macros.expand(l)
                if len(l) == 2 and l[0].upper() == 'NOWARN':
                    warn=0
                    l=l[1:]
                else:
                    warn=1

                if len(l) != 1:
                    error("REPEATENDING: Use [NoWarn] Count")

                count=stoi(l[0], "RepeatEnding takes an integer arg")

                if count < 0:
                    error("RepeatEnding count must be postive, not '%s'" % count)

                elif count == 0 and warn:
                    warning("RepeatEnding count of 0, skipping section")

                elif count == 1 and warn:
                    warning("RepeatEnding count of 1 duplicates default")

                elif count > 10 and warn:
                    warning("%s is a large value for RepeatEnding" % count)
            else:
                count = 1

            rpt, rptnum, act, l = repeatChunk()

            for c in range(count):
                stack.extend(main)
                stacknum.extend(mainnum)
                stack.extend(rpt)
                stacknum.extend(rptnum)


        else:
            error("Unexpected line in REPEAT")

def goto(ln):
    if len(ln) != 1:
        error("Usage: GOTO Label")
    gbl.inpath.goto(ln[0].upper())

def eof(ln):
        gbl.inpath.toEof()


#######################################
# Tempo/timing


def setTime(ln):
    """ Set the 'time sig'.

        We do restrict the time setting to the range of 1..12.
        No particular reason, but we do need some limit? Certainly
        it has to be greater than 0.
    """

    if len(ln) != 1:
        error("Use: Time N")

    n = stoi(ln[0], "Argument for time must be integer")

    if n < 1 or n > 12:
        error("Time (beats/bar) must be 1..12")

    # If no change, just ignore this.

    if gbl.QperBar != n:
        gbl.QperBar = int(n)

        # Time changes zap all predfined sequences

        for a in gbl.tnames.values():
            a.clearSequence()


def tempo(ln):
    """ Set tempo. """

    if not ln or len(ln) >2:
        error("Use: Tempo [*,+,-]BperM [BARS]")

    # Get new value.

    a = ln[0][0]
    if a in "+-*":
        v = stof(ln[0][1:], "Tempo expecting value for rate adjustment, not '%s'" % ln[0])
        if a == '-':
            v = gbl.tempo - v
        elif a == '+':
            v += gbl.tempo
        elif a == '*':
            v *= gbl.tempo

    else:
        v  = stof(ln[0], "Tempo expecting rate, not '%s'" % ln[0])


    # is this immediate or over time?

    if len(ln) == 1:
        gbl.tempo = int(v)
        gbl.mtrks[0].addTempo(gbl.tickOffset, gbl.tempo)
        if gbl.debug:
            print "Set Tempo to %s" % gbl.tempo


    else:         # Do a tempo change over bar count
        bars = ln[1]

        bars = stof(bars, "Expecting value, not %s" % bars )
        numbeats = int(bars * gbl.QperBar)

        if numbeats < 1:
            error("Beat count must be greater than 1")

        # Vary the rate in the meta track

        tincr = (v - gbl.tempo) / float(numbeats)    # incr per beat
        bstart = gbl.tickOffset            # start
        boff = 0
        tempo = gbl.tempo

        for n in range(numbeats):
            tempo += tincr
            if tempo:
                gbl.mtrks[0].addTempo(bstart + boff, int(tempo))
            boff += gbl.BperQ

        if tempo != v:
            gbl.mtrks[0].addTempo(bstart + boff, int(v) )

        gbl.tempo = int(v)

        if gbl.debug:
            print "Set future Tempo to %s over %s beats" % \
                ( int(tempo), numbeats)


def beatAdjust(ln):
    """ Delete or insert some beats into the sequence.

        This just adjusts the current song position. Nothing is
        lost or added to the actual file.
    """


    if len(ln) != 1:
        error("Use: BeatAdjust NN")

    adj = stof(ln[0], "Expecting a value (not %s) for BeatAdjust" % ln[0])

    gbl.tickOffset += int(adj * gbl.BperQ)

    if gbl.debug:
        print "BeatAdjust: inserted %s at bar %s." % (adj, gbl.barNum + 1)


def cut(ln):
    """ Insert a all-note-off into all tracks. """

    if not len(ln):
        ln=['0']

    if len(ln) != 1:
        error("Use: Cut Offset")

    """ Loop though all the tracks. Note that trackCut() checks
        to make sure that there is a need to insert in specified track.
        In this loop we create a list of channels as we loop though
        all the tracks, skipping over any duplicate channels or
        tracks with no channel assigned.
    """

    l=[]
    for t in sorted(gbl.tnames.keys()):
        c = gbl.tnames[t].channel
        if not c or c in l:
            continue
        l.append(c)
        trackCut(t, ln)


def fermata(ln):
    """ Apply a fermata timing to the specified beat. """

    if len(ln) != 3:
        error("Use: Fermata 'offset' 'duration' 'adjustment'")

    offset = stof(ln[0], "Expecting a value (not '%s') "
              "for Fermata Offset" % ln[0] )

    if offset < -gbl.QperBar or offset > gbl.QperBar:
        warning("Fermata: %s is a large beat offset" % offset)

    dur = stof(ln[1], "Expecting a value (not '%s') for Fermata Duration" % ln[1])

    if dur <= 0:
        error("Fermata duration must be greater than 0")

    if dur > gbl.QperBar:
        warning("Fermata: %s is a large duration" % dur)

    adj = stof(ln[2], "Expecting a value (not '%s') for Fermata Adjustment" % ln[2])

    if adj< 100:
        warning("Fermata: Adjustment less than 100 is shortening beat value")

    if adj == 100:
        error("Fermata: using value of 100 makes no difference, must be an error")

    moff=int(gbl.tickOffset + (gbl.BperQ * offset))

    if moff < 0:
        error("Fermata offset comes before track start")

    gbl.mtrks[0].addTempo(moff, int(gbl.tempo / (adj/100)) )

    tickDur = int(gbl.BperQ * dur)

    gbl.mtrks[0].addTempo(moff + tickDur, gbl.tempo)

    # Clear out NoteOn events in all tracks

    if offset < 0:
        start = moff + int(.05 * gbl.BperQ)
        end = moff + tickDur - int(.05 * gbl.BperQ)

        for n, tr in gbl.mtrks.items():
            if n <= 0: continue        # skip meta track
            tr.zapRangeTrack(start, end )

    if gbl.debug:
        print "Fermata: Beat %s, Duration %s, Change %s, Bar %s" % \
              (offset, dur, adj, gbl.barNum + 1)
        if offset < 0:
            print "\tNoteOn Events removed in tick range %s to %s" \
                  % (start, end)


#######################################
# Groove stuff


def grooveDefine(ln):
    """ Define a groove.

        Current settings are assigned to a groove name.
    """

    if not len(ln):
        error("Use: DefGroove  Name")

    slot=ln[0].upper()

    # Slot names can't contain a '/' (reserved) or be an integer (used in groove select).

    if '/' in slot:
        error("The '/' is not permitted in a groove name")

    if slot.isdigit():
        error("Invalid slot name '%s'. Cannot be only digits" % slot)

    grooveDefineDo(slot)

    if gbl.debug:
        print "Groove settings saved to '%s'." % slot

    if gbl.makeGrvDefs:
        MMA.auto.updateGrooveList(slot)

    if len(ln) > 1:
        MMA.docs.docDefine(ln)


def grooveDefineDo(slot):

    for n in gbl.tnames.values():
        n.saveGroove(slot)

    gbl.settingsGroove[slot] = {
        'SEQSIZE':   gbl.seqSize,
        'SEQRNDWT':  seqRndWeight[:],
        'QPERBAR':   gbl.QperBar,
        'SEQRND':    gbl.seqRnd[:],
        'TIMESIG':   MMA.midi.timeSig.get(),
        '81':        MMA.notelen.noteLenTable['81'],
        '82':        MMA.notelen.noteLenTable['82'],
        'SWINGMODE': gbl.swingMode ,
        'SWINGSKEW': gbl.swingSkew,
        'VRATIO':    (MMA.volume.vTRatio, MMA.volume.vMRatio)}


def groove(ln):
    """ Select a previously defined groove. """

    global groovesList, groovesCount

    if not ln:
        error("Groove: needs agrument(s)")

    tmpList =[]

    if ln[0].isdigit():
        wh=stoi(ln[0])
        if wh<1:
            error("Groove selection must be > 0, not '%s'" % wh)
        ln=ln[1:]
    else:
        wh = None

    for slot in ln:
        slot = slot.upper()
        if slot == "/":
            if len(tmpList):
                slot=tmpList[-1]
            else:
                error("A previous groove name is needed before a '/'")

        if not slot in gbl.settingsGroove:

            if gbl.debug:
                print "Groove '%s' not defined. Trying auto-load from libraries" \
                      % slot

            l=MMA.auto.loadGrooveDir(slot)    # name of the lib file with groove

            if l:
                if gbl.debug:
                    print "Attempting to load groove '%s' from '%s'." \
                      % (slot, l)

                usefile([os.path.join(gbl.autoLib, l)])

                if not slot in gbl.settingsGroove:
                    error("Groove '%s' not found. Have libraries changed "
                          "since last 'mma -g' run?" % slot)

            else:
                error("Groove '%s' could not be found in memory or library files" % slot )

        tmpList.append(slot)

    if not len(tmpList):
        error("Use: Groove [selection] Name [...]")

    """ If the first arg to list was an int() (ie: 3 groove1 groove2 grooveFoo)
        we select from the list. After the selection, we reset the list to be
        just the selected entry. This was, if there are multiple groove names without
        a leading int() we process the list as groove list changing with each bar.
    """

    if wh:
        wh = (wh-1) % len(tmpList)
        tmpList=tmpList[wh:wh+1]

    slot=tmpList[0]
    grooveDo(slot)

    groovesCount = 0
    if len(tmpList)==1:
        groovesList=None
    else:
        groovesList=tmpList

    gbl.lastGroove = gbl.currentGroove
    gbl.currentGroove = slot
    if gbl.lastGroove == '':
        gbl.lastGroove = slot

    if gbl.debug:
        print "Groove settings restored from '%s'." % slot

def grooveDo(slot):
    """ This is separate from groove() so we can call it from
        usefile() with a qualified name. """

    global seqRndWeight

    oldSeqSize = gbl.seqSize

    g=gbl.settingsGroove[slot]

    gbl.seqSize      = g['SEQSIZE']
    seqRndWeight  = g['SEQRNDWT']
    gbl.QperBar      = g['QPERBAR']
    gbl.seqRnd    = g['SEQRND']
    MMA.midi.timeSig.set( *g['TIMESIG'])  # passing tuple as 2 args.
    MMA.notelen.noteLenTable['81'] = g['81']
    MMA.notelen.noteLenTable['82'] = g['82']
    gbl.swingMode = g['SWINGMODE']
    gbl.swingSkew = g['SWINGSKEW']
    MMA.volume.vTRatio, MMA.volume.vMRatio = g['VRATIO']

    for n in gbl.tnames.values():
        n.restoreGroove(slot)

    """ This is important! Tracks NOT overwritten by saved grooves way
        have the wrong sequence length. I don't see any easy way to hit
        just the unchanged/unrestored tracks so we do them all.
        Only done if a change in seqsize ... doesn't take long to be safe.
    """

    if oldSeqSize != gbl.seqSize:
        for a in gbl.tnames.values():
            a.setSeqSize()

    seqRndWeight = MMA.pat.seqBump(seqRndWeight)

    gbl.seqCount = 0

def grooveClear(ln):
    """ Delete all previously loaded grooves from memory."""

    global groovesList, groovesCount

    if ln:
        error("GrooveClear does not have any arguments.")

    groovesList = {}
    groovesCount = 0
    
    try:
        a= gbl.settingsGroove[gmagic]
    except:
        a=None

    gbl.settingsGroove={}

    if a:
        gbl.settingsGroove[gmagic]=a

    gbl.lastGroove = ''
    gbl.currentGroove = ''


    if gbl.debug:
        print "All grooves deleted."
    
#######################################
# File and I/O

def include(ln):
    """ Include a file. """

    global beginData

    if beginData:
        error("INCLUDE not permitted in Begin/End block")

    if len(ln) != 1:
        error("Use:     Include FILE" )

    fn = MMA.file.locFile(ln[0], gbl.incPath)
    if not fn:
        error("Could not find include file '%s'" % ln)

    else:
        parseFile(fn)


def usefile(ln):
    """ Include a library file. """

    global beginData

    if beginData:
        error("USE not permitted in Begin/End block")

    if len(ln) != 1:
        error("Use: Use FILE")

    ln = ln[0]
    fn = MMA.file.locFile(ln, gbl.libPath)

    if not fn:
        error("Unable to locate library file '%s'" % ln)

    """ USE saves current state, just like defining a groove.
        Here we use a magic number which can't be created with
        a defgroove ('cause it's an integer). Save, read, restore.
    """

    slot = gmagic
    grooveDefineDo(slot)
    parseFile(fn)
    grooveDo(slot)


def mmastart(ln):
    if not ln:
        error ("Use: MMAstart FILE [file...]")

    gbl.mmaStart.extend(ln)

    if gbl.debug:
        print "MMAstart set to:",
        printList(ln)

def mmaend(ln):
    if not ln:
        error ("Use: MMAend FILE [file...]")

    gbl.mmaEnd.extend(ln)

    if gbl.debug:
        print "MMAend set to:",
        printList(ln)


def setLibPath(ln):
    """ Set the LibPath variable.  """

    if len(ln) > 1:
        error("Only one path can be entered for LibPath")

    f = os.path.expanduser(ln[0])

    if gbl.debug:
        print "LibPath set to", f

    gbl.libPath = f


def setAutoPath(ln):
    """ Set the autoPath variable.    """

    if len(ln) > 1:
        error("Only one path can be entered for AutoLibPath")

    f = os.path.expanduser(ln[0])

    MMA.auto.grooveDir = {}

    # To avoid conflicts, delete all existing grooves (current seq not effected)

    gbl.settingsGroove = {}
    gbl.lastGroove = ''
    gbl.currentGroove = ''

    if gbl.debug:
        print "AutoLibPath set to", f

    gbl.autoLib = f


def setIncPath(ln):
    """ Set the IncPath variable.  """

    if len(ln)>1:
        error("Only one path is permitted in SetIncPath")

    f = os.path.expanduser(ln[0])

    if gbl.debug:
        print "IncPath set to", f

    gbl.incPath=f


def setOutPath(ln):
    """ Set the Outpath variable. """

    if not ln:
        gbl.outPath = ""

    elif len(ln) > 1:
        error ("Use: SetOutPath PATH")

    else:
        gbl.outPath = os.path.expanduser(ln[0])



#######################################
# Sequence

def seqsize(ln):
    """ Set the length of sequences. """

    global seqRndWeight

    if len(ln) !=1:
        error("Usage 'SeqSize N'")

    n = stoi(ln[0], "Argument for SeqSize must be integer")

    # Setting the sequence size always resets the seq point

    gbl.seqCount = 0

    """ Now set the sequence size for each track. The class call
        will expand/contract existing patterns to match the new
        size.
    """

    if n != gbl.seqSize:
        gbl.seqSize = n
        for a in gbl.tnames.values():
            a.setSeqSize()

        seqRndWeight = seqBump(seqRndWeight)

    if gbl.debug:
        print "Set SeqSize to ", n


def seq(ln):
    """ Set the sequence point. """

    if len(ln) == 0:
        s = 0
    elif len(ln)==1:
        s = stoi(ln[0], "Expecting integer value after SEQ")
    else:
        error("Use: SEQ or SEQ NN to reset seq point")


    if s > gbl.seqSize:
        error("Sequence size is '%d', you can't set to '%d'" %
              (gbl.seqSize, s))

    if s==0:
        s=1

    if s<0:
        error("Seq parm must be greater than 0, not %s", s)

    gbl.seqCount = s-1

    if gbl.seqRnd[0] == 1:
        warning("SeqRnd has been disabled by a Seq command")
        seqRnd = [0]


def seqClear(ln):
    """ Clear all sequences (except SOLO tracks). """

    if ln:
        error ("Use: 'SeqClear' with no args")

    for n in gbl.tnames.values():
        if n.vtype != "SOLO":
            n.clearSequence()
    MMA.volume.futureVol = []

    setSeqRndWeight(['1'])


def setSeqRnd(ln):
    """ Set random order for all tracks. """

    emsg =  "use [ON, OFF | TrackList ]"
    if not ln:
        error("SeqRnd:" + emsg)

    a=ln[0].upper()

    if a in ("ON", "1") and len(ln) == 1:
        gbl.seqRnd = [1]

    elif a in ("OFF", "0") and len(ln) == 1:
        gbl.seqRnd = [0]

    else:
        gbl.seqRnd=[2]
        for a in ln:
            a = a.upper()
            if not a in gbl.tnames:
                error("SeqRnd: Track '%s' does not exist, %s" % (a, emsg))
            if a in gbl.seqRnd:
                error("SeqRnd: Duplicate track '%s' specified, %s" % (a, emsg))
            gbl.seqRnd.append(a)

    if gbl.debug:
        print "SeqRnd:",
        if gbl.seqRnd[0] == 2:
            for a in gbl.seqRnd[1:]:
                print a,
            print
        else:
            if gbl.seqRnd[0] == 1:
                print "On"
            else:
                print "Off"


def setSeqRndWeight(ln):
    """ Set global rnd weight. """

    global seqRndWeight

    if not ln:
        error("Use: RndWeight <weight factors>")

    tmp = []
    for n in ln:
        n = stoi(n)
        if n < 0: error("RndWeight: Values must be 0 or greater")
        tmp.append(n)

    seqRndWeight = seqBump(tmp)

    if gbl.debug:
        print "RndWeight: ",
        printList(seqRndWeight)


def restart(ln):
    """ Restart all tracks to almost-default condidions. """

    if ln:
        error ("Use: 'Restart' with no args")

    for n in gbl.tnames.values():
        n.restart()


#######################################
# Midi

def midiMarker(ln):
    """ Parse off midi marker. """

    if len(ln) == 2:
        offset = stof(ln[0])
        msg = ln[1]
    elif len(ln) == 1:
        offset = 0
        msg = ln[0]
    else:
        error("Usage: MidiMark [offset] Label")

    offset = int(gbl.tickOffset + (gbl.BperQ * offset))
    if offset < 0:
        error("MidiMark offset points before start of file")

    gbl.mtrks[0].addMarker(offset, msg)


def rawMidi(ln):
    """ Send hex bytes as raw midi stream. """

    mb=''
    for a in ln:
        a=stoi(a)

        if a<0 or a >0xff:
            error("All values must be in the range "
                  "0 to 0xff, not '%s'" % a)

        mb += chr(a)

    gbl.mtrks[0].addToTrack(gbl.tickOffset, mb)

    if gbl.debug:
        print "Inserted raw midi in metatrack: ",
        for b in mb:
            print '%02x' % ord(b),
        print


def mdefine(ln):
    """ Set a midi seq pattern. """

    if not ln:
        error("MDefine needs arguments")

    name = ln[0]
    if name.startswith('_'):
        error("Names with a leading underscore are reserved")

    if name.upper() == 'Z':
        error("The name 'Z' is reserved")

    MMA.mdefine.mdef.set(name, ' '.join(ln[1:]))


def setMidiFileType(ln):
    """ Set some MIDI file generation flags. """

    if not ln:
        error("USE: MidiFile [SMF=0/1] [RUNNING=0/1]")

    for l in ln:
        try:
            mode, val = l.upper().split('=')
        except:
            error("Each arg must contain an '=', not '%s'" % l)

        if mode == 'SMF':
            if val == '0':
                gbl.midiFileType = 0
            elif val == '1':
                gbl.midiFileType = 1
            else:
                error("Use: MIDIFile SMF=0/1")

            if gbl.debug:
                print "Midi Filetype set to", gbl.midiFileType


        elif mode == 'RUNNING':
            if val == '0':
                gbl.runningStatus = 0
            elif val == '1':
                gbl.runningStatus = 1
            else:
                error("Use: MIDIFile RUNNING=0/1")

            if gbl.debug:
                print "Midi Running Status Generation set to",
                if gbl.runningStatus:
                    print 'ON (Default)'
                else:
                    print 'OFF'


        else:
            error("Use: MIDIFile [SMF=0/1] [RUNNING=0/1]")


def setChPref(ln):
    """ Set MIDI Channel Preference. """

    if not ln:
        error("Use: ChannelPref TRACKNAME=CHANNEL [...]")

    for i in ln:
        if '=' not in i:
            error("Each item in ChannelPref must have an '='")

        n,c = i.split('=')

        c = stoi(c, "Expecting an integer for ChannelPref, not '%s'" % c)

        if c<1 or c>16:
            error("Channel for ChannelPref must be 1..16, not %s" % c)

        gbl.midiChPrefs[n.upper()]=c

    if gbl.debug:
        print "ChannelPref:",
        for n,c in gbl.midiChPrefs.items():
            print "%s=%s" % (n,c),
        print


def setTimeSig(ln):
    """ Set the midi time signature. """

    if len(ln) == 1:
        a=ln[0].upper()
        if a == 'COMMON':
            ln=('4','4')
        elif a == 'CUT':
            ln=('2','2')

    if len(ln) != 2:
        error("TimeSig: Usage (num dem) or ('cut' or 'common')")

    nn = stoi(ln[0])

    if nn<1 or nn>126:
        error("Timesig NN must be 1..126")

    dd = stoi(ln[1])
    if     dd == 1:  dd = 0
    elif dd == 2:  dd = 1
    elif dd == 4:  dd = 2
    elif dd == 8:  dd = 3
    elif dd == 16: dd = 4
    elif dd == 32: dd = 5
    elif dd == 64: dd = 6
    else:
        error("Unknown value for timesig denominator")

    MMA.midi.timeSig.set(nn,dd)




#######################################
# Misc


def rndseed(ln):
    """ Reseed the random number generator. """

    if not ln:
        random.seed()

    elif len(ln)>1:
        error("RNDSEED: requires 0 or 1 arguments")
    else:
        random.seed(stof(ln[0]))

def transpose(ln):
    """ Set transpose value. """


    if len(ln) != 1:
        error("Use: Transpose N")

    t = stoi(ln[0], "Argument for Tranpose must be an integer, not '%s'" % ln[0])
    if t < -12 or t > 12:
            error("Tranpose %s out-of-range; must be -12..12" % t)

    gbl.transpose = t

    if gbl.debug:
        print "Set Transpose to %s" % t


def lnPrint(ln):
    """ Print stuff in a "print" command. """

    print " ".join(ln)


def printActive(ln):
    """ Print a list of the active tracks. """

    print "Active tracks, groove:", gbl.currentGroove, ' '.join(ln)

    for a in sorted(gbl.tnames.keys()):
        f=gbl.tnames[a]
        if f.sequence:
            print "     ",a
    print


def setDebug(ln):
    """ Set debugging options dynamically. """

    msg=( "Use: Debug MODE=On/Off where MODE is one or more of "
          "DEBUG, FILENAMES, PATTERNS, SEQUENCE, "
          "RUNTIME, WARNINGS or EXPAND" )


    if not len(ln):
        error(msg)

        # save current flags

        gbl.Ldebug       = gbl.debug
        gbl.LshowFilenames = gbl.showFilenames
        gbl.Lpshow       = gbl.pshow
        gbl.Lseqshow       = gbl.seqshow
        gbl.Lshowrun       = gbl.showrun
        gbl.LnoWarn       = gbl.noWarn
        gbl.LnoOutput       = gbl.noOutput
        gbl.LshowExpand       = gbl.showExpand
        gbl.Lchshow       = gbl.chshow


    for l in ln:
        try:
            mode, val = l.upper().split('=')
        except:
            error("Each debug option must contain a '=', not '%s'" % l)

        if val == 'ON' or val == '1':
            setting = 1
        elif val == 'OFF' or val == '0':
            setting = 0
        else:
            error(msg)

        if mode == 'DEBUG':
            gbl.debug = setting
            if gbl.debug:
                print "Debug=%s." % val

        elif mode == 'FILENAMES':
            gbl.showFilenames = setting
            if gbl.debug:
                print "ShowFilenames=%s." % val

        elif mode == 'PATTERNS':
            gbl.pshow = setting
            if gbl.debug:
                print "Pattern display=%s." % val

        elif mode == 'SEQUENCE':
            gbl.seqshow = setting
            if gbl.debug:
                print "Sequence display=%s." % val

        elif mode == 'RUNTIME':
            gbl.showrun = setting
            if gbl.debug:
                print "Runtime display=%s." % val

        elif mode == 'WARNINGS':
            gbl.noWarn = not(setting)
            if gbl.debug:
                print "Warning display=%s" % val

        elif mode == 'EXPAND':
            gbl.showExpand = setting
            if gbl.debug:
                print "Expand display=%s." % val

        else:
            error(msg)



###########################################################
###########################################################
## Track specific commands


#######################################
# Pattern/Groove

def trackDefPattern(name, ln):
    """ Define a pattern for a track.

    Use the type-name for all defines.... check the track
    names and if it has a '-' in it, we use only the
    part BEFORE the '-'. So DRUM-Snare becomes DRUM.
    """

    ln=ln[:]

    name=name.split('-')[0]

    trackAlloc(name, 1)

    if ln:
        pattern = ln.pop(0).upper()
    else:
        error("Define is expecting a pattern name")

    if pattern in ('z', 'Z', '-'):
        error("Pattern name '%s' is reserved" % pattern)

    if pattern.startswith('_'):
        error("Names with a leading underscore are reserved")

    if not ln:
        error("No pattern list given for '%s %s'" % (name, pattern) )

    ln=' '.join(ln)
    gbl.tnames[name].definePattern(pattern, ln)


def trackSequence(name, ln):
    """ Define a sequence for a track.

    The format for a sequence:
    TrackName Seq1 [Seq2 ... ]

    Note, that SeqX can be a predefined seq or { seqdef }
    The {} is dynamically interpreted into a def.
    """

    if not ln:
        error ("Use: %s Sequence NAME [...]" % name)

    ln = ' '.join(ln)

    """ Extract out any {} definitions and assign them to new
    define variables (__1, __99, etc) and melt them
    back into the string.
    """

    ids=1
    while 1:
        sp = ln.find("{")

        if sp<0:
            break

        ln, s = pextract(ln, "{", "}", 1)
        if not s:
            error("Did not find matching '}' for '{'")

        pn = "_%s" % ids
        ids+=1

        trk=name.split('-')[0]
        trackAlloc(trk, 1)

        gbl.tnames[trk].definePattern(pn, s[0])
        ln = ln[:sp] + ' ' + pn + ' ' + ln[sp:]

    ln=ln.split()

    gbl.tnames[name].setSequence(ln)


def trackSeqClear(name,     ln):
    """ Clear sequence for specified tracks.

    Note: "Drum SeqClear" clears all Drum tracks,
          "Drum-3 SeqClear" clears track Drum-3.
    """

    if ln:
        error("No args permitted. Use %s SEQCLEAR" % name)

    for n in gbl.tnames:
        if n.find(name) == 0:
            if gbl.debug:
                print "SeqClear: Track %s cleared." % n
            gbl.tnames[n].clearSequence()


def trackSeqRnd(name, ln):
    """ Set random order for specified track. """

    if len(ln) != 1:
        error("Use: %s SeqRnd [On, Off]" % name)

    gbl.tnames[name].setRnd(ln[0].upper())

def trackSeqRndWeight(name, ln):
    """ Set rnd weight for track. """

    if not ln:
        error("Use: %s RndWeight <weight factors>" % name)

    gbl.tnames[name].setRndWeight(ln)


def trackRestart(name, ln):
    """ Restart track to almost-default condidions. """

    if ln:
        error ("Use: '%s Resart' with no args", name)

    gbl.tnames[name].restart()



def trackGroove(name, ln):
    """ Select a previously defined groove for a single track. """

    if len(ln) != 1:
        error("Use: %s Groove Name" % name)


    slot = ln[0].upper()

    if not slot in gbl.settingsGroove:
        error("Groove '%s' not defined" % slot)

    g=gbl.tnames[name]
    g.restoreGroove(slot)

    if g.sequence == [None] * len(g.sequence):
        warning("'%s' Track Groove has no sequence. Track name error?" % name)

    g.setSeqSize()

    if gbl.debug:
        print "%s Groove settings restored from '%s'." % (name, slot)


def trackRiff(name, ln):
    """ Set a riff for a track. """

    gbl.tnames[name].setRiff(' '.join(ln))



def deleteTrks(ln):
    """ Delete a track and free the MIDI track. """

    if not len(ln):
        error("Use Delete Track [...]")

    for name in ln:
        name=name.upper()
        if name in gbl.tnames:
            tr = gbl.tnames[name]
        else:
            error("Track '%s' does not exist" % name)

        if tr.channel:
            tr.doMidiClear()
            tr.clearPending()

            if tr.riff:
                warning("%s has pending RIFF(s)" % name)
            gbl.midiAvail[tr.channel] -= 1

            # NOTE: Don't try deleting 'tr' since it's just a copy!!

            del gbl.tnames[name]

        if not name in gbl.deletedTracks:
            gbl.deletedTracks.append(name)

        if gbl.debug:
            print "Track '%s' deleted" % name



#######################################
# Volume

def trackRvolume(name, ln):
    """ Set random volume for specific track. """

    if not ln:
        error ("Use: %s RVolume N [...]" % name)

    gbl.tnames[name].setRVolume(ln)


def trackCresc(name, ln):
    gbl.tnames[name].setCresc(1, ln)

def trackDeCresc(name, ln):
    gbl.tnames[name].setCresc(-1, ln)

def trackVolume(name, ln):
    """ Set volume for specific track. """

    if not ln:
        error ("Use: %s Volume DYN [...]" % name)

    gbl.tnames[name].setVolume(ln)


def trackChannelVol(name, ln):
    """ Set the channel volume for a track."""

    if len(ln) != 1:
        error("Use: %s ChannelVolume" % name)

    v=stoi(ln[0], "Expecting integer arg, not %s" % ln[0])

    if v<0 or v>127:
        error("ChannelVolume must be 0..127")

    gbl.tnames[name].setChannelVolume(v)


def trackAccent(name, ln):
    """ Set emphasis beats for track."""

    gbl.tnames[name].setAccent(ln)


#######################################
# Timing

def trackCut(name, ln):
    """ Insert a ALL NOTES OFF at the given offset. """


    if not len(ln):
        ln=['0']

    if    len(ln) != 1:
        error("Use: %s Cut Offset" % name)


    offset = stof(ln[0], "Cut offset expecting value, (not '%s')" % ln[0])

    if offset < -gbl.QperBar or offset > gbl.QperBar:
        warning("Cut: %s is a large beat offset" % offset)



    moff = int(gbl.tickOffset + (gbl.BperQ * offset))

    if moff < 0:
        error("Calculated offset for Cut comes before start of track")

    """ Insert allnoteoff directly in track. This skips the normal
    queueing in pats because it would never take if at the end
    of a track.
    """

    m = gbl.tnames[name].channel
    if m and len(gbl.mtrks[m].miditrk) > 1:
        gbl.mtrks[m].addNoteOff(moff)


        if gbl.debug:
            print "%s Cut: Beat %s, Bar %s" % (name, offset, gbl.barNum + 1)


def trackMallet(name, ln):
    """ Set repeating-mallet options for solo/melody track. """

    if not ln:
        error("Use: %s Mallet <Option=Value> [...]" % name)

    gbl.tnames[name].setMallet(ln)


def trackRtime(name, ln):
    """ Set random timing for specific track. """

    if not ln:
        error ("Use: %s RTime N [...]" % name)


    gbl.tnames[name].setRTime(ln)


def trackRskip(name, ln):
    """ Set random skip for specific track. """

    if not ln:
        error ("Use: %s RSkip N [...]" % name)


    gbl.tnames[name].setRSkip(ln)


def trackArtic(name, ln):
    """ Set articulation. """

    if not ln:
        error("Use: %s Articulation N [...]" % name)


    gbl.tnames[name].setArtic(ln)


#######################################
# Chord stuff


def trackCompress(name, ln):
    """ Set (unset) compress for track. """

    if not ln:
        error("Use: %s Compress <value[s]>" % name)

    gbl.tnames[name].setCompress(ln)


def trackVoicing(name, ln):
    """ Set Voicing options. Only valid for chord tracks at this time."""

    if not ln:
        error("Use: %s Voicing <MODE=VALUE> [...]" % name)


    gbl.tnames[name].setVoicing(ln)



def trackDupRoot(name, ln):
    """ Set (unset) the root note duplication. Only applies to chord tracks. """

    if not ln:
        error("Use: %s DupRoot <value> ..." % name)

    gbl.tnames[name].setDupRoot(ln)


def trackChordLimit(name, ln):
    """ Set (unset) ChordLimit for track. """

    if len(ln) != 1:
        error("Use: %s ChordLimit <value>" % name)

    gbl.tnames[name].setChordLimit(ln[0])

def trackRange(name, ln):
    """ Set (unset) Range for track. Only effects arp and scale. """

    if not ln:
        error("Use: %s Range <value> ... " % name)


    gbl.tnames[name].setRange(ln)


def trackInvert(name, ln):
    """ Set invert for track."""

    if not ln:
        error("Use: %s Invert N [...]" % name)

    gbl.tnames[name].setInvert(ln)


def trackSpan(name, ln):
    """ Set midi note span for track. """

    if len(ln) != 2:
        error("Use: %s Start End" % name)

    start = stoi(ln[0], "Expecting integer for SPAN 1st arg")
    if start <0 or start >127:
        error("Start arg for Span must be 0..127, not %s" % start)

    end = stoi(ln[1], "Expecting integer for SPAN 2nd arg")
    if end <0 or end >127:
        error("End arg for Span must be 0..127, not %s" % end)

    if end <= start:
        error("End arg for Span must be greater than start")

    if end-start < 11:
        error("Span range must be at least 12")

    gbl.tnames[name].setSpan(start, end)



def trackOctave(name, ln):
    """ Set octave for specific track. """

    if not ln:
        error ("Use: %s Octave N [...], (n=0..10)" % name)


    gbl.tnames[name].setOctave( ln )


def trackStrum(name, ln):
    """ Set all specified track strum. """

    if not ln:
        error ("Use: %s Strum N [...]" % name)


    gbl.tnames[name].setStrum( ln )


def trackHarmony(name, ln):
    """ Set harmony value. """

    if not ln:
        error("Use: %s Harmony N [...]" % name)

    gbl.tnames[name].setHarmony(ln)


def trackHarmonyOnly(name, ln):
    """ Set harmony only for track. """

    if not ln:
        error("Use: %s HarmonyOnly N [...]" % name)

    gbl.tnames[name].setHarmonyOnly(ln)

def trackHarmonyVolume(name, ln):
    """ Set harmony volume for track."""

    if not ln:
        error("Use: %s HarmonyVolume N [...]" % name)

    gbl.tnames[name].setHarmonyVolume(ln)


#######################################
# MIDI setting


def trackChannel(name, ln):
    """ Set the midi channel for a track."""

    if not ln:
        error("Use: %s Channel" % name)

    gbl.tnames[name].setChannel(ln[0])


def trackMdefine(name, ln):
    """ Set a midi seq pattern. Ignore track name."""

    mdefine(ln)


def trackMidiExt(ln):
    """ Helper for trackMidiSeq() and trackMidiVoice()."""

    ids=1
    while 1:
        sp = ln.find("{")

        if sp<0:
            break

        ln, s = pextract(ln, "{", "}", 1)
        if not s:
            error("Did not find matching '}' for '{'")

        pn = "_%s" % ids
        ids+=1

        MMA.mdefine.mdef.set(pn, s[0])
        ln = ln[:sp] + ' ' + pn + ' ' + ln[sp:]

    return ln.split()


def trackMidiClear(name, ln):
    """ Set MIDI command to send at end of groove. """

    if not ln:
        error("Use %s MIDIClear Controller Data" % name)


    if len(ln) == 1 and ln[0] == '-':
        gbl.tnames[name].setMidiClear( '-' )
    else:
        ln=' '.join(ln)
        if '{' in ln or '}' in ln:
            error("{}s are not permitted in %s MIDIClear command" % name)
        gbl.tnames[name].setMidiClear( trackMidiExt( '{' + ln + '}' ))


def trackMidiSeq(name, ln):
    """ Set reoccurring MIDI command for track. """

    if not ln:
        error("Use %s MidiSeq Controller Data" % name)

    if len(ln) == 1 and ln[0]== '-':
        gbl.tnames[name].setMidiSeq('-')
    else:
        gbl.tnames[name].setMidiSeq( trackMidiExt(' '.join(ln) ))


def trackMidiVoice(name, ln):
    """ Set single shot MIDI command for track. """

    if not ln:
        error("Use %s MidiVoice Controller Data" % name)

    if len(ln) == 1 and ln[0] == '-':
        gbl.tnames[name].setMidiVoice( '-' )
    else:
        gbl.tnames[name].setMidiVoice( trackMidiExt(' '.join(ln) ))


def trackChShare(name, ln):
    """ Set MIDI channel sharing."""

    if len(ln) !=1:
        error("Use: %s ChShare TrackName" % name)

    gbl.tnames[name].setChShare(ln[0])


def trackVoice(name, ln):
    """ Set voice for specific track. """

    if not ln:
        error ("Use: %s Voice NN [...]" % name)


    gbl.tnames[name].setVoice(ln)


def trackPan(name, ln):
    """ Set the Midi Pan value for a track."""

    if len(ln) != 1:
        error("Use: %s PAN NN" % name)

    gbl.tnames[name].setPan(ln[0])


def trackOff(name, ln):
    """ Turn a track off """

    if ln:
        error("Use: %s OFF with no paramater" % name)

    gbl.tnames[name].setOff()


def trackOn(name, ln):
    """ Turn a track on """

    if ln:
        error("Use: %s ON with no paramater" % name)

    gbl.tnames[name].setOn()


def trackMidiName(name,ln):
    """ Set channel track name."""

    if not ln:
        error("Use: %s TrackName" % name)

    gbl.tnames[name].setTname(ln[0])


def trackTone(name, ln):
    """ Set the tone (note). Only valid in drum tracks."""

    if not ln:
        error("Use: %s Tone N [...]" % name)

    gbl.tnames[name].setTone(ln)


def trackGlis(name, ln):
    """ Enable/disable portamento. """

    if len(ln) != 1:
        error("Use: %s Portamento NN, off=0, 1..127==on" % name)

    gbl.tnames[name].setGlis(ln[0])

def trackForceOut(name, ln):
    """ Force output of voice settings. """

    if len(ln):
        error("Use %s ForceOut (no options)" % name)

    gbl.tnames[name].setForceOut()


#######################################
# Misc

def trackDrumType(name, ln):
    """ Set a melody or solo track to be a drum solo track."""

    tr = gbl.tnames[name]
    if tr.vtype not in ('SOLO', 'MELODY'):
        error ("Only Solo and Melody tracks can be to DrumType, not '%s'" % name)
    if ln:
        error("No parmeters permitted for DrumType command")

    tr.setDrumType()


def trackDirection(name, ln):
    """ Set scale/arp direction. """

    if not ln:
        error("Use: %s Direction OPT" % name)


    gbl.tnames[name].setDirection(ln)


def trackScaletype(name, ln):
    """ Set the scale type. """

    if not ln:
        error("Use: %s ScaleType OPT" % name)

    gbl.tnames[name].setScaletype(ln)


def trackCopy(name, ln):
    """ Copy setting in 'ln' to 'name'. """

    if len(ln) != 1:
        error("Use: %s Copy ExistingTrack" % name)

    gbl.tnames[name].copySettings(ln[0].upper())


def trackUnify(name, ln):
    """ Set UNIFY for track."""

    if not len(ln):
        error("Use %s UNIFY 1 [...]" % name)

    gbl.tnames[name].setUnify(ln)



""" =================================================================

    Command jump tables. These need to be at the end of this module
    to avoid undefined name errors. The tables are only used in
    the parse() function.

    The first table is for the simple commands ... those which DO NOT
    have a leading trackname. The second table is for commands which
    require a leading track name.

    The alphabetic order is NOT needed, just convenient.

"""

simpleFuncs={
    'ADJUSTVOLUME':     MMA.volume.adjvolume,
    'ALLTRACKS':        allTracks,
    'AUTHOR':           MMA.docs.docAuthor,
    'AUTOSOLOTRACKS':   MMA.patSolo.setAutoSolo,
    'BEATADJUST':       beatAdjust,
    'CHANNELPREF':      setChPref,
    'COMMENT':          comment,
    'CRESC':            MMA.volume.setCresc,
    'CUT':              cut,
    'DEBUG':            setDebug,
    'DEC':              macros.vardec,
    'DECRESC':          MMA.volume.setDecresc,
    'DEFCHORD':         MMA.chords.defChord,
    'DEFGROOVE':        grooveDefine,
    'DELETE':           deleteTrks,
    'DOC':              MMA.docs.docNote,
    'DOCVAR':           MMA.docs.docVars,
    'DRUMVOLTR':        MMA.translate.drumVolTable.set,
    'ELSE':             ifelse,
    'ENDIF':            ifend,
    'ENDMSET':          endmset,
    'ENDREPEAT':        repeatend,
    'EOF':              eof,
    'FERMATA':          fermata,
    'GOTO':             goto,
    'GROOVE':           groove,
    'GROOVECLEAR':      grooveClear,
    'IF':               macros.varIF,
    'IFEND':            ifend,
    'INC':              macros.varinc,
    'INCLUDE':          include,
    'KEYSIG':           MMA.patSolo.keySig.set,
    'LABEL':            comment,
    'LYRIC':            lyric.option,
    'MIDIDEF':          mdefine,
    'MIDI':             rawMidi,
    'MIDIFILE':         setMidiFileType,
    'MIDIINC':          MMA.midiIn.midiinc,
    'MIDIMARK':         midiMarker,
    'MIDISPLIT':        MMA.midi.setSplitChannels,
    'MMAEND':           mmaend,
    'MMASTART':         mmastart,
    'MSET':             macros.msetvar,
    'MSETEND':          endmset,
    'NEWSET':           macros.newsetvar,
    'CHORDADJUST':      MMA.chords.chordAdjust,
    'PRINT':            lnPrint,
    'PRINTACTIVE':      printActive,
    'PRINTCHORD':       MMA.chords.printChord,
    'REPEAT':           repeat,
    'REPEATEND':        repeatend,
    'REPEATENDING':     repeatending,
    'RESTART':          restart,
    'RNDSEED':          rndseed,
    'RNDSET':           macros.rndvar,
    'SEQ':              seq,
    'SEQCLEAR':         seqClear,
    'SEQRND':           setSeqRnd,
    'SEQRNDWEIGHT':     setSeqRndWeight,
    'SEQSIZE':          seqsize,
    'SET':              macros.setvar,
    'SETAUTOLIBPATH':   setAutoPath,
    'SETINCPATH':       setIncPath,
    'SETLIBPATH':       setLibPath,
    'SETOUTPATH':       setOutPath,
    'SHOWVARS':         macros.showvars,
    'STACKVALUE':       macros.stackValue,
    'SWINGMODE':        MMA.notelen.swingMode,
    'TEMPO':            tempo,
    'TIME':             setTime,
    'TIMESIG':          setTimeSig,
    'TONETR':           MMA.translate.dtable.set,
    'UNSET':            macros.unsetvar,
    'USE':              usefile,
    'VARCLEAR':         macros.clear,
    'VEXPAND':          macros.vexpand,
    'VOICEVOLTR':       MMA.translate.voiceVolTable.set,
    'VOICETR':          MMA.translate.vtable.set,
    'VOLUME':           MMA.volume.setVolume,
    'TRANSPOSE':        transpose
}


trackFuncs={
    'ACCENT':          trackAccent,
    'ARTICULATE':      trackArtic,
    'CHANNEL':         trackChannel,
    'MIDIVOLUME':      trackChannelVol,
    'CHSHARE':         trackChShare,
    'COMPRESS':        trackCompress,
    'COPY':            trackCopy,
    'CRESC':           trackCresc,
    'CUT':             trackCut,
    'DECRESC':         trackDeCresc,
    'DIRECTION':       trackDirection,
    'DRUMTYPE':        trackDrumType,
    'DUPROOT':         trackDupRoot,
    'FORCEOUT':        trackForceOut,
    'GROOVE':          trackGroove,
    'HARMONY':         trackHarmony,
    'HARMONYONLY':     trackHarmonyOnly,
    'HARMONYVOLUME':   trackHarmonyVolume,
    'INVERT':          trackInvert,
    'LIMIT':           trackChordLimit,
    'MALLET':          trackMallet,
    'MIDIDEF':         trackMdefine,
    'MIDIGLIS':        trackGlis,
    'MIDICLEAR':       trackMidiClear,
    'MIDIPAN':         trackPan,
    'MIDIGLIS':        trackGlis,
    'MIDISEQ':         trackMidiSeq,
    'MIDITNAME':       trackMidiName,
    'MIDIVOICE':       trackMidiVoice,
    'OCTAVE':          trackOctave,
    'OFF':             trackOff,
    'ON':              trackOn,
    'RANGE':           trackRange,
    'RESTART':         trackRestart,
    'RIFF':            trackRiff,
    'RSKIP':           trackRskip,
    'RTIME':           trackRtime,
    'RVOLUME':         trackRvolume,
    'SCALETYPE':       trackScaletype,
    'SEQCLEAR':        trackSeqClear,
    'SEQRND':          trackSeqRnd,
    'SEQUENCE':        trackSequence,
    'SEQRNDWEIGHT':    trackSeqRndWeight,
    'NOTESPAN':        trackSpan,
    'STRUM':           trackStrum,
    'TONE':            trackTone,
    'UNIFY':           trackUnify,
    'VOICE':           trackVoice,
    'VOICING':         trackVoicing,
    'VOLUME':          trackVolume,
    'DEFINE':          trackDefPattern
}


