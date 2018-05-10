
# macros.py

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

The macros are stored, set and parsed in this single-instance
class. At the top of MMAparse an instance in created with
something like:     macros=MMMmacros.Macros().
"""

import gbl
from   MMA.common import *
from   MMA.notelen import getNoteLen
import MMA.midiC
import MMA.lyric
import MMA.translate
import MMA.patSolo
import MMA.patAria
import MMA.volume
import MMA.notelen

import random


class Macros:

    vars={}            # storage
    expandMode = 1        # flag for variable expansion
    pushstack = []

    def __init__(self):

        self.vars={}

    def clear(self, ln):
        if ln:
            error("VarClear does not take an argument.")
        self.vars={}
        if gbl.debug:
            print "All variable definitions cleared."

    def stackValue(self, s):
        self.pushstack.append(' '.join(s))


    def sysvar(self, s):
        """ Create an internal macro. """

        # Simple/global     system values

        if s == 'KEYSIG':
            a=MMA.patSolo.keySig.kSig
            if a >= 0:
                f='#'
            else:
                f='b'
            return "%s%s" % (abs(a), f)

        elif s == 'TIME':
            return str(gbl.QperBar)

        elif s == 'TEMPO':
            return str(gbl.tempo)

        elif s == 'VOLUME':
            return    str(int(MMA.volume.volume * 100))  # INT() is important

        elif s == 'VOLUMERATIO':
            return str((MMA.volume.vTRatio * 100))

        elif s == 'LASTVOLUME':
            return str(int(MMA.volume.lastVolume * 100))

        elif s == 'GROOVE':
            return gbl.currentGroove

        elif s == 'LASTGROOVE':
            return gbl.lastGroove

        elif s == 'SEQRND':
            if gbl.seqRnd[0] == 0: return "Off"
            if gbl.seqRnd[0] == 1: return "On"
            return ' '.join(gbl.seqRnd[1:])

        elif s == 'SEQSIZE':
            return str(gbl.seqSize)

        elif s == 'SWINGMODE':
            if gbl.swingMode:
                a = "On"
            else:
                a = "Off"
            return "%s Skew=%s" % (a, gbl.swingSkew)

        elif s == 'TRANSPOSE':
            return str(gbl.transpose)

        elif s == 'STACKVALUE':
            if not self.pushstack:
                error( "Empty push/pull variable stack")
            return self.pushstack.pop()

        elif s == 'DEBUG':
            return "Debug=%s  Filenames=%s Patterns=%s " \
                    "Sequence=%s Runtime=%s Warnings=%s Expand=%s" % \
                    (gbl.debug, gbl.showFilenames, gbl.pshow, gbl.seqshow, \
                    gbl.showrun,  int(not gbl.noWarn), gbl.showExpand)


        elif s == 'LASTDEBUG':
            return "Debug=%s  Filenames=%s Patterns=%s " \
                    "Sequence=%s Runtime=%s Warnings=%s Expand=%s" % \
                    (gbl.Ldebug, gbl.LshowFilenames, gbl.Lpshow, gbl.Lseqshow, \
                    gbl.Lshowrun,  int(not gbl.LnoWarn), gbl.LshowExpand)

        elif s == 'VEXPAND':
            if self.expandMode:
                return "On"
            else:
                return "Off"

        elif s == "MIDISPLIT":
            return ' '.join([str(x) for x in MMA.midi.splitChannels])

        elif s == 'SEQRNDWEIGHT':
            return ' '.join([str(x) for x in MMA.parse.seqRndWeight])

        elif s == 'AUTOLIBPATH':
            return gbl.autoLib

        elif s == 'LIBPATH':
            return gbl.libPath

        elif s == 'INCPATH':
            return gbl.incPath

        elif s == 'VOICETR':
            return MMA.translate.vtable.retlist()

        elif s == 'TONETR':
            return MMA.translate.dtable.retlist()

        elif s == 'OUTPATH':
            return gbl.outPath

        elif s == 'BARNUM':
            return str(gbl.barNum + 1)

        elif s == 'LINENUM':
            return str(gbl.lineno)

        elif s == 'LYRIC':
            return MMA.lyric.lyric.setting()

        # Track vars ... these are in format TRACKNAME_VAR

        a=s.rfind('_')
        if a==-1:
            error("Unknown system variable $_%s" % s)

        tname = s[:a]
        func = s[a+1:]

        if gbl.tnames.has_key(tname):
            t=gbl.tnames[tname]
        else:
            error("System variable $_%s refers to nonexistent track" % s)


        if func == 'ACCENT':
            r=[]
            for s in t.accent:
                r.append("{")
                for b,v in s:
                    r.append(str((b/gbl.BperQ)+1))
                    r.append(str(int(v * 100)))
                r.append("}")
            return ' '.join(r)

        elif func == 'ARTICULATE':
            return ' '.join([str(x) for x in t.artic])

        elif func == 'CHANNEL':
            return str(t.channel)

        elif func == 'COMPRESS':
            return ' '.join([str(x) for x in t.compress])

        elif func == 'DIRECTION':
            if t.vtype == 'ARIA':
                return ' '.join([str(x) for x in t.selectDir])
            else:
                return ' '.join([str(x) for x in t.direction])

        elif func == 'DUPROOT':
            if t.vtype != "CHORD":
                error("Only CHORD tracks have DUPROOT")
            return ' '.join([str(x) for x in t.dupRoot])

        elif func == 'HARMONY':
            return ' '.join([str(x) for x in t.harmony])

        elif func == 'HARMONYVOLUME':
            return ' '.join([str(int(a * 100)) for a in t.harmonyVolume])

        elif func == 'INVERT':
            return ' '.join([str(x) for x in t.invert])

        elif func == 'LIMIT':
            return str( t.chordLimit )

        elif func == 'MALLET':
            if t.vtype not in ("SOLO", "MELODY"):
                error("Mallet only valid in SOLO and MELODY tracks")
            return "Mallet Rate=%i Decay=%i" % (t.mallet, t.malletDecay*100)

        elif func == 'OCTAVE':
            return ' '.join([str(a/12) for a in t.octave])

        elif func == 'RANGE':
            return ' '.join([str(x) for x in t.chordRange])

        elif func == 'RSKIP':
            return ' '.join([str(int(a * 100)) for a in t.rSkip])

        elif func == 'RTIME':
            return ' '.join([str(x) for x in t.rTime])

        elif func == 'RVOLUME':
            return ' '.join([str(int(a * 100)) for a in t.rVolume])

        elif func == 'SEQRND':
            if t.seqRnd: return 'On'
            else:        return 'Off'

        elif func == 'SEQRNDWEIGHT':
            return ' '.join([str(x) for x in t.seqRndWeight])

        elif func == 'SPAN':
            return "%s %s" % (t.spanStart, t.spanEnd)

        elif func == 'STRUM':
            if t.vtype != "CHORD":
                error("Only CHORD tracks have STRUM")
            return ' '.join([str(x) for x in t.strum])

        elif func == 'TONE':
            if t.vtype != "DRUM":
                error("Only DRUM tracks have TONE")
            return ' '.join([MMA.midiC.valueToDrum(a) for a in t.toneList])

        elif func == 'UNIFY':
            return ' '.join([str(x) for x in t.unify])

        elif func == 'VOICE':
            return ' '.join([MMA.midiC.voiceNames[a] for a in t.voice])

        elif func == 'VOICING':
            if t.vtype != 'CHORD':
                error("Only CHORD tracks have VOICING")
            t=t.voicing
            return "Mode=%s Range=%s Center=%s RMove=%s Move=%s Dir=%s" % \
                (t.mode, t.range, t.center, t.random, t.bcount, t.dir)

        elif func == 'VOLUME':
            return ' '.join([str(int(a * 100)) for a in t.volume])

        else:
            error("Unknown system track variable %s" % s)



    def expand(self, l):
        """ Loop though input line and make variable subsitutions.
            MMA variables are pretty simple ... any word starting
            with a "$xxx" is a variable.

            l - list

            RETURNS: new list with all subs done.
        """

        if not self.expandMode:
            return l

        while 1:          # Loop until no more subsitutions have been done
            sub=0
            for i,s in enumerate(l):
                if s[:2] == '$$':
                    continue

                if s[0]=='$':
                    s=s[1:].upper()

                    if s.startswith('_'):
                        ex=self.sysvar(s[1:])

                    elif not s in self.vars:
                        error("User variable '%s'  has not been defined" % s )

                    else:
                        ex=self.vars[s]

                    if type(ex) == type([]):    # MSET variable
                        if len(ex):
                            gbl.inpath.push( ex[1:], [gbl.lineno] * len(ex[1:]))
                            if len(ex):
                                ex=ex[0]
                            else:
                                ex=[]
                    else:                       # regular SET variable
                        ex=ex.split()

                    l=l[:i] + ex + l[i+1:]    # ex might be a list, so this is needed
                    sub=1
                    break

            if not sub:
                break

        return l


    def showvars(self, ln):
        """ Display all currently defined variables. """

        if len(ln):
            for a in ln:
                a=a.upper()
                if a in self.vars:
                    print "$%s: %s" % (a, self.vars[a])
                else:
                    print "$%s - not defined" % a

        else:

            print "User variables defined:"
            kys = self.vars.keys()
            kys.sort()

            mx = 0

            for a in kys:                    # get longest name
                if len(a) > mx:
                    mx = len(a)

            mx = mx + 2

            for a in kys:
                print "     %-*s  %s" % (mx, '$'+a, self.vars[a])

    def getvname(self, v):
        """ Helper routine to validate variable name. """

        if v[0] in ('$', '_'):
            error("Variable names cannot start with a '$' or '_'")
        return v.upper()

    def rndvar(self, ln):
        """ Set a variable randomly from a list. """

        if len(ln) < 2:
            error("Use: RndSet Variable_Name <list of possible values>")

        v = self.getvname(ln[0])

        self.vars[v] = random.choice(ln[1:])

        if gbl.debug:
            print "Variable $%s randomly set to '%s'" % (v, self.vars[v])

    def newsetvar(self, ln):
        """ Set a new variable. Ignore if already set. """

        if not len(ln):
            error("Use: NSET VARIABLE_NAME [Value] [[+] [Value]]")

        if self.getvname(ln[0]) in self.vars:
            return

        self.setvar(ln)

    def setvar(self, ln):
        """ Set a variable. Not the difference between the next 2 lines:
                Set Bar BAR
                Set Foo AAA BBB $bar
                   $Foo == "AAA BBB BAR"
                Set Foo AAA + BBB + $bar
                   $Foo == "AAABBBBAR"

            The "+"s just strip out interveing spaces.
        """

        if len(ln) < 1:
            error("Use: SET VARIABLE_NAME [Value] [[+] [Value]]")

        v=self.getvname(ln.pop(0))

        t=''
        addSpace = 0
        for i,a in enumerate(ln):
            if a == '+':
                addSpace = 0
                continue
            else:
                if addSpace:
                    t += ' '
                t += a
                addSpace = 1


        self.vars[v]=t

        if gbl.debug:
            print "Variable $%s == '%s'" % (v, self.vars[v])


    def msetvar(self, ln):
        """ Set a variable to a number of lines. """

        if len(ln) !=1:
            error("Use: MSET VARIABLE_NAME <lines> MsetEnd")

        v=self.getvname(ln[0])

        lm=[]

        while 1:
            l=gbl.inpath.read()
            if not l:
                error("Reached EOF while looking for MSetEnd")
            cmd=l[0].upper()
            if cmd in ("MSETEND", 'ENDMSET'):
                if len(l) > 1:
                    error("No arguments permitted for MSetEnd/EndMSet")
                else:
                    break
            lm.append(l)

        self.vars[v]=lm


    def unsetvar(self, ln):
        """ Delete a variable reference. """


        if len(ln) != 1:
            error("Use: UNSET Variable")
        v=ln[0].upper()
        if v[0] == '_':
            error("Internal variables cannot be deleted or modified")

        if v in self.vars:
            del(macros.vars[v])

            if gbl.debug:
                print "Variable '%s' UNSET" % v
        else:
            warning("Attempt to UNSET nonexistent variable '%s'" % v)


    def vexpand(self, ln):

        if len(ln) == 1:
            cmd = ln[0].upper()
        else:
            cmd=''

        if cmd == 'ON':
            self.expandMode=1
            if gbl.debug:
                print "Variable expansion ON"

        elif cmd == 'OFF':
            self.expandMode=0
            if gbl.debug:
                print "Variable expansion OFF"

        else:
            error("Use: Vexpand ON/Off")


    def varinc(self, ln):
        """ Increment  a variable. """

        if len(ln) == 1:
            inc=1

        elif len(ln) == 2:
            inc = stof(ln[1], "Expecting a value (not %s) for Inc" % ln[1])

        else:
            error("Usage: INC Variable [value]")

        v=ln[0].upper()

        if v[0] == '_':
            error("Internal variables cannot be modified")

        if not v in self.vars:
            error("Variable '%s' not defined" % v)

        vl=stoi(self.vars[v], "Variable must be a value to increment") + inc

        if vl == int(vl):
            vl = int(vl)
        self.vars[v]=str(vl)

        if gbl.debug:
            print "Variable '%s' INC to %s" % (v, self.vars[v])


    def vardec(self, ln):
        """ Decrement a varaiable. """

        if len(ln) == 1:
            dec = 1

        elif len(ln) == 2:
            dec = stof(ln[1], "Expecting a value (not %s) for Inc" % ln[1])

        else:
            error("Usage: DEC Variable [value]")

        v=ln[0].upper()
        if v[0] == '_':
            error("Internal variables cannot be modified")

        if not v in self.vars:
            error("Variable '%s' not defined" % v)

        vl=stoi(self.vars[v], "Variable must be a value to decrement") - dec

        if vl == int(vl):
            vl = int(vl)

        self.vars[v]=str(vl)

        if gbl.debug:
            print "Variable '%s' DEC to %s" % (v, self.vars[v])


    def varIF(self, ln):
        """ Conditional variable if/then. """

        def expandV(l):
            """ Private func. """

            l=l.upper()

            if l[:2] == '$$':
                l=l[2:]
                if not l in self.vars:
                    error("String Variable '%s' does not exist" % l)
                l=self.vars[l]

            try:
                v=float(l)
            except:
                v=None

            return ( l, v )


        def readblk():
            """ Private, reads a block until ENDIF, IFEND or ELSE.
                Return (Terminator, lines[], linenumbers[] )
            """

            q=[]
            qnum=[]
            nesting=0

            while 1:
                l=gbl.inpath.read()
                if not l:
                    error("EOF reached while looking for EndIf")

                cmd=l[0].upper()
                if cmd == 'IF':
                    nesting+=1
                if cmd in ("IFEND", 'ENDIF', 'ELSE'):
                    if len(l) > 1:
                        error("No arguments permitted for IfEnd/EndIf/Else")
                    if not nesting:
                        break
                    if cmd != 'ELSE':
                        nesting -= 1

                q.append(l)
                qnum.append(gbl.lineno)

            return (cmd, q, qnum)


        if len(ln)<2:
            error("Usage: IF <Operator> ")

        action = ln[0].upper()

        # 1. do the unary options: DEF, NDEF

        if action in ('DEF', 'NDEF'):
            if len(ln) != 2:
                error("Usage: IF %s VariableName" % action)

            v=ln[1].upper()
            retpoint = 2

            if action == 'DEF':
                compare = self.vars.has_key(v)
            elif action == 'NDEF':
                compare = ( not self.vars.has_key(v))
            else:
                error("Unreachable unary conditional")


        # 2. Binary ops: EQ, NE, etc.

        elif action in ('LT', 'LE', 'EQ', 'GE', 'GT', 'NE'):
            if len(ln) != 3:
                error("Usage: VARS %s Value1 Value2" % action)


            s1,v1 = expandV(ln[1])
            s2,v2 = expandV(ln[2])

            if type(v1) == type(1.0) and type(v2) == type(1.0):
                s1=v1
                s2=v2


            retpoint = 3

            if     action == 'LT':
                compare = (v1 <     v2)
            elif action == 'LE':
                compare = (v1 <= v2)
            elif action == 'EQ':
                compare = (v1 == v2)
            elif action == 'GE':
                compare = (v1 >= v2)
            elif action == 'GT':
                compare = (v1 >     v2)
            elif action == 'NE':
                compare = (v1 != v2)
            else:
                error("Unreachable binary conditional")

        else:
            error("Usage: IF <CONDITON> ...")


        """ Go read until end of if block.
            We shove the block back if the compare was true.
            Unless, the block is terminated by an ELSE ... then we need
            to read another block and push back one of the two.
        """

        cmd, q, qnum = readblk()


        if cmd == 'ELSE':
            cmd, q1, qnum1 = readblk()

            if cmd == 'ELSE':
                error("Only one ELSE is permitted in IF construct")

            if not compare:
                compare = 1
                q = q1
                qnum = qnum1

        if compare:
            gbl.inpath.push( q, qnum )


macros = Macros()
