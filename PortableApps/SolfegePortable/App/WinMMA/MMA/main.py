
# main.py

"""
The program "MMA - Musical Midi Accompaniment" and the associated
modules distributed with it are protected by copyright.

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
import gbl
from   MMA.common import *
import MMA.midi
import MMA.docs
import MMA.parse
from   MMA.file import locFile
from   MMA.lyric import lyric
import MMA.options

########################################
########################################

# This is the program mainline. It is called/executed
# exactly once from a call in the stub program mma.py.

###########################


# Get our command line stuff

MMA.options.opts()

"""
    LibPath and IncPath are set in MMA.globals. Debug setting isn't set
    when the default is done.
"""

if gbl.debug:
    print "Initialization has set LibPath set to", gbl.libPath
    print "Initialization has set IncPath set to", gbl.incPath


#######################################
# Set up initial meta track stuff. Track 0 == meta

m = gbl.mtrks[0] = MMA.midi.Mtrk(0)

m.addText(0, "Created by MMA.")
m.addTrkName(0, 'MetaTrack')
m.addTempo(0, gbl.tempo)
MMA.parse.setTimeSig(['4','4'])   # most stdlib files will override this


#####################################
# Read an RC file. All found files are processed.

docOption = gbl.docs   # Disable doc printing for RC file
gbl.docs = 0

rcread=0

rcfiles = ('mmarc', 'c:\\mma\\mmarc', '~/.mmarc', '/usr/local/etc/mmarc', '/etc/mmarc'    )
if gbl.mmaRC:
    rcfiles = [ gbl.mmaRC ]

for i in rcfiles:
    f = locFile(i, None)
    if f:
        if gbl.showrun:
            print "Reading RC file '%s'" % f
        MMA.parse.parseFile(f)
        rcread+=1
        break
    else:
        if gbl.mmaRC:
            error("Specified init file '%s' not found" % gbl.mmaRC)

if not rcread:
    gbl.lineno = -1
    warning("No RC file was found or processed")


gbl.docs = docOption   # Restore doc options


################################################
# Update the library database file(s) (-g option)
# Note: This needs to be here, after reading of RC files

if gbl.makeGrvDefs:
    if gbl.infile:
        error("No filename is permitted with the -g option")
    from MMA.auto import libUpdate
    libUpdate()                # update and EXIT


################################
# We need an input file for anything after this point.

if not gbl.infile:
    MMA.options.usage("No input filename specified.")

# Add filename to meta track.

gbl.mtrks[0].addText(0, "Input filename: %s" % gbl.infile)

################################
# Just extract docs (-Dx) to stdout.

if docOption:
    f=locFile(gbl.infile, None)
    if not f:
        error("File '%s' not found" % gbl.infile)
    MMA.parse.parseFile(f)
    sys.exit(0)


#########################################################
# These cmdline options override settings in RC files

if gbl.cmdSMF:
    gbl.lineno = -1
    MMA.parse.setMidiFileType(['SMF=%s' % gbl.cmdSMF])


##########################################
# Create the output filename.
# If outfile was specified on cmd line then leave it alone.
#    Otherwise ...
#    1. strip off the extension if it is .mma,
#    2. append .mid

if gbl.outfile:
    outfile = gbl.outfile
else:
    outfile, ext = os.path.splitext(gbl.infile)
    if ext != gbl.ext:
        outfile=gbl.infile
    outfile += '.mid'


outfile=os.path.expanduser(outfile)


################################################
# Read/process files....

# First the mmastart files

for f in gbl.mmaStart:
    fn = locFile(f, gbl.incPath)
    if not fn:
        warning("MmaStart file '%s' not found/processed" % fn)
    MMA.parse.parseFile(fn)
    gbl.lineno = -1

# The song file specified on the command line

f = locFile(gbl.infile, None)

if not f:
    gbl.lineno = -1
    error("Input file '%s' not found" % gbl.infile)

MMA.parse.parseFile(f)

# Finally, the mmaend files

for f in gbl.mmaEnd:
    fn = locFile(f, None)
    if not fn:
        warning("MmaEnd file '%s' not found/processed" % f)
    MMA.parse.parseFile(fn)


#################################################
# Just display the channel assignments (-c) and exit...

if gbl.chshow:
    print "\nFile '%s' parsed, but no MIDI file produced!" % gbl.infile
    print
    print "Tracks allocated:"
    k=gbl.tnames.keys()
    k.sort()
    max=0
    for a in k + gbl.deletedTracks:
        if len(a)>max:
            max = len(a)
    max+=1
    wrap=0
    for a in k:
        wrap += max
        if wrap>60:
            wrap = max
            print
        print " %-*s" %( max, a),
    print
    print
    if gbl.deletedTracks:
        print "Deleted Tracks:"
        wrap=0
        for a in gbl.deletedTracks:
            wrap += max
            if wrap>60:
                wrap=max
                print
            print " %-*s" %( max,a),
        print
        print
    print "Channel assignments:"
    for c, n in sorted(gbl.midiAssigns.items()):
        if n:
            wrap = 3
            print " %2s" % c,
            for nn in n:
                wrap += max
                if wrap>63:
                    print "\n   ",
                    wrap=max+3
                print "%-*s" % (max,nn),

            print
    print
    sys.exit(0)


####################################
# Dry run, no output

if gbl.noOutput:
    warning( "Input file parsed successfully. No midi file generated")
    sys.exit(0)


##############################
# Create the output (MIDI) file

gbl.lineno=-1    # disable line nums for error/warning

""" We fix the outPath now. This lets you set outpath in the song file.

    The filename "outfile" was created above. It is either the input filename
    with '.mma' changed to '.mid' OR if -f<FILE> was used then it's just <FILE>.

    If any of the following is true we skip inserting the outputpath into the
    filename:

        - if outfile starts with a '/'
        - if outPath was not set
        - if -f was used

    Next, the outPath is inserted into the filename. If outPath starts with
    a ".", "/" or "\ " then it is inserted at the start of the path;
    otherwise it is inserted before the filename portion.
"""

if (not outfile.startswith('/')) and gbl.outPath and (not gbl.outfile):
    if gbl.outPath[0] in '.\\/':
        outfile = "%s/%s" % (gbl.outPath, outfile)
    else:
        head, tail = os.path.split(outfile)
        outfile = "%s/%s/%s" % (head, gbl.outPath, tail)

fileExist = os.path.exists(outfile)

""" Check if any pending midi events are still around. Mostly
    this will be a DRUM event which was assigned to the 'DRUM'
    track, but no DRUM track was used, just DRUM-xx tracks used.
"""

for n in gbl.tnames.values():
    if n.channel:
        n.doMidiClear()
        n.clearPending()
        if n.riff:
            warning("%s has pending Riff(s)" % n.name)

""" Check all the tracks and find total number used. When
    initializing each track (class) we made an initial entry
    in the track at offset 0 for the track name, etc. So, if the
    track only has one entry we can safely skip the entire track.
"""

trackCount=1    # account for meta track

for n in sorted(gbl.mtrks.keys())[1:]:     # check all but 0 (meta)
    if len(gbl.mtrks[n].miditrk) > 1:
        trackCount += 1

if trackCount == 1: # only meta track
    if fileExist:
        print
    print "No data created. Did you remember to set a groove/sequence?"
    if fileExist:
        print "Existing file '%s' has not been modified." % outfile
    sys.exit(1)

lyric.leftovers()

if fileExist:
    print "Overwriting existing",
else:
    print "Creating new",
print "midi file (%s bars): '%s'" %  (gbl.barNum, outfile)

try:
    out = file(outfile, 'wb')
except:
    error("Can't open file '%s' for writing" % outfile)

MMA.midi.writeTracks(out)
out.close()

if gbl.debug:
    print "Completed processing file '%s'." % outfile

