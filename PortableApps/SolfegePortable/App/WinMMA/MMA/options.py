# opts.py

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




import getopt
import sys

import gbl
from   MMA.common import *
import MMA.docs
import MMA.parse
import MMA.alloc
import MMA.chords
from   MMA.macro import macros


def opts():
    """ Option parser. """

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],
            "dpsS:ri:wneom:f:M:cgGvD:0", [] )


    except getopt.GetoptError:
        usage()

    for o,a in opts:
        
        if o == '-d':
            gbl.debug = gbl.Ldebug = 1

        elif o == '-o':
            gbl.showFilenames = gbl.LshowFilenames = 1

        elif o == '-p':
            gbl.pshow = gbl.Lpshow = 1

        elif o == '-s':
            gbl.seqshow = gbl.Lseqshow = 1

        elif o == '-S':
            ln = a.split('=', 1)
            macros.setvar(ln)

        elif o == '-r':
            gbl.showrun = gbl.Lshowrun = 1

        elif o == '-w':
            gbl.noWarn = gbl.LnoWarn = 1

        elif o == '-n':
            gbl.noOutput = gbl.LnoOutput = 1

        elif o == '-e':
            gbl.showExpand = gbl.LshowExpand = 1

        elif o == '-c':
            gbl.chshow = gbl.Lchshow = 1

        elif o == '-f':
            gbl.outfile = a

        elif o == '-i':
            gbl.mmaRC = a

        elif o == '-g':
            gbl.makeGrvDefs = 1

        elif o == '-G':
            gbl.makeGrvDefs = 2

        elif o == '-m':
            try:
                a=int(a)
            except:
                error("Expecting -m arg to be a integer")
            gbl.maxBars = a

        elif o == '-v':
            print "%s" % gbl.version
            sys.exit(0)

        elif o == '-M':
            if a in ['0', '1']:
                gbl.cmdSMF = a
            else:
                error("Only a '0' or '1' is permitted for the -M arg")

        elif o == '-D':
            if a == 'xl':
                gbl.docs = 1

            elif a == 'xh':
                gbl.docs = 2

            elif a == 'k':

                def pl(msg, lst):
                    print msg,
                    for i in sorted(lst.keys()):
                        print i,
                    print "\n"

                pl("Base track names:", MMA.alloc.trkClasses )
                pl("Commands:", MMA.parse.simpleFuncs)
                pl("TrackCommands:", MMA.parse.trackFuncs)
                print "Not complete ... subcommands, comments, chords..."
                sys.exit(0)

            else:
                print "Unknown -D option."
                usage()

        elif o == '-0':
            gbl.synctick = 1

        else:
            usage()      # unreachable??

    if args:
        if gbl.infile:
            usage("Only one input filename is permitted.")
        gbl.infile = args.pop(0)


def usage(msg=''):
    """ Usage message. """

    txt=[
        "MMA - Musical Midi Accompaniment",
        "  Copyright 2003-5, Bob van der Poel. Version %s" % gbl.version ,
        "  Distributed under the terms of the GNU Public License.",
        "  Usage: mma [opts ...] INFILE [opts ...]",
        "",
        "Options:",
        " -c    display default Channel assignments",
        " -d    enable lots of Debugging messages",
        " -Dk   print list of MMA keywords",
        " -Dxl  eXtract Latex doc blocks from file",
        " -Dxh  eXtract HTML doc blocks from file",
        " -e    show parsed/Expanded lines",
        " -f <file>  set output Filename",
        " -g    update Groove dependency database",
        " -G    create Groove dependency database",
        " -i <file> specify init (mmarc) file",
        " -m <x> set Maxbars (default == 500)",
        " -M <x> set SMF to 0 or 1",
        " -n    No generation of midi output",
        " -o    show complete filenames when Opened",
        " -p    display Patterns as they are defined",
        " -r    display Running progress",
        " -s    display Sequence info during run",
        " -S <var[=data]>  Set macro 'var' to 'data'",
        " -v    display Version number",
        " -w    disable Warning messages",
        " -0    create sync at start of all channel tracks" ]


    for a in txt:
        print a

    if msg:
        print
        print msg

    print
    sys.exit(1)


