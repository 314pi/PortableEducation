
# translate.py

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


This module handles voice name translations.

"""

import gbl
import MMA.midiC
from   MMA.common import *


""" Translation table for VOICE. This is ONLY used when a voice is set
    from the VOICE command. If a translation exists the translation is
    substituted.
"""


class Vtable:

    def __init__(self):
        self.table = {}

    def retlist(self):

        l=[]
        for n in sorted(self.table.keys()):
            l.append("%s=%s" % (n.title(), self.table[n]))

        return ' '.join(l)


    def set(self, ln):
        """ Set a name/alias for voice translation, called from parser. """

        if not ln:
            self.table = {}
            if gbl.debug:
                print "Voice Translaion table reset."

            return

        for l in ln:
            l=l.upper()
            if l.count('=') != 1:
                error("Each translation pair must be in the format Voice=Alias")
            v,a = l.split('=')
            self.table[v] = a

        if gbl.debug:
            print "Voice Translations: ",
            for l in ln:
                print l,
            print

    def get(self, name):
        """ Return a translation or original. """

        name=name.upper()
        if self.table.has_key(name):
            return self.table[name]

        else:
            return name

vtable=Vtable()            # Create single class instance.


""" This is just like the Vtable, but it is used for DRUM TONES. We use
    this translation when a TONE is set for a drum in setTone() and when a
    tone is selected in a Solo/Melody DRUM track.
"""

class Dtable:

    def __init__(self):
        self.table = {}

    def retlist(self):

        l=[]
        for n in sorted(self.table.keys()):
            l.append("%s=%s" %  ( MMA.midiC.valueToDrum(n),
                                  MMA.midiC.valueToDrum(self.table[n])))

        return ' '.join(l)


    def set(self, ln):
        """ Set a name/alias for drum tone translation, called from parser. """

        if not ln:
            self.table = {}
            if gbl.debug:
                print "DrumTone Translaion table reset."

            return

        for l in ln:
            l=l.upper()
            if l.count('=') != 1:
                error("Each translation pair must be in the format Voice=Alias")
            v,a = l.split('=')

            v=MMA.midiC.drumToValue(v)
            a=MMA.midiC.drumToValue(a)

            self.table[v] = a
            if gbl.debug:
                print "DrumTone Translation: %s=%s" % \
                      (MMA.midiC.valueToDrum(v), MMA.midiC.valueToDrum(a))


    def get(self, name):
        """ Return a translation or original. """

        v=MMA.midiC.drumToValue(name)

        if self.table.has_key(v):
            return self.table[v]

        else:
            return v



dtable=Dtable()


""" Volume adjustment. Again, similar to voice/tone translations,
    but this is for the volume. The table creates a percentage adjustment
    for tones/voices specified. When a TRACK VOLUME is set in
    MMApat.setVolume() the routine checks here for an adjustment.
"""

class VoiceVolTable:

    def __init__(self):
        self.table = {}

    def retlist(self):
        l=[]
        for n in sorted(self.table.keys()):
            l.append("%s=%s" %  ( MMA.midiC.valueToInst(n), self.table[n]))

        return ' '.join(l)


    def set(self, ln):
        """ Set a name/alias for voice volume adjustment, called from parser. """

        if not ln:
            self.table = {}
            if gbl.debug:
                print "Voice Volume Adjustment table reset."

            return

        for l in ln:
            l=l.upper()
            if l.count('=') != 1:
                error("Each translation pair must be in the format Voice=Ajustment")
            v,a = l.split('=')

            v=MMA.midiC.instToValue(v)
            a=stoi(a)
            if a<1 or a>200:
                error("Voice volume adjustments must be in range 1 to 200, not %s" % a)
            self.table[v] = a/100.
            if gbl.debug:
                print "Voice Volume Adjustment: %s=%s" % (MMA.midiC.valueToInst(v), a)


    def get(self, v, vol):
        """ Return an adjusted value or original. """

        if self.table.has_key(v):
            vol = int(vol * self.table[v])

        return vol


voiceVolTable=VoiceVolTable()

class DrumVolTable:

    def __init__(self):
        self.table = {}

    def retlist(self):

        l=[]
        for n in sorted(self.table.keys()):
            l.append("%s=%s" %  ( MMA.midiC.valueToDrum(n), self.table[n]))

        return ' '.join(l)


    def set(self, ln):
        """ Set a name/alias for voice volume adjustment, called from parser. """

        if not ln:
            self.table = {}
            if gbl.debug:
                print "Drum Volume Adjustment table reset."

            return

        for l in ln:
            l=l.upper()
            if l.count('=') != 1:
                error("Each translation pair must be in the format Drum=Ajustment")
            v,a = l.split('=')

            v=MMA.midiC.instToValue(v)
            a=stoi(a)
            if a<1 or a>200:
                error("Drum volume adjustments must be in range 1 to 200, not %s" % a)
            self.table[v] = a/100.
            if gbl.debug:
                print "Drum Volume Adjustment: %s=%s" % (MMA.midiC.valueToDrum(v), a)


    def get(self, v, vol):
        """ Return an adjusted value or original. """

        if self.table.has_key(v):
            vol = int(vol * self.table[v])

        return vol


drumVolTable=DrumVolTable()


