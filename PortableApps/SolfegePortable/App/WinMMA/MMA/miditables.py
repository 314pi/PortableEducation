
# miditables.py

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

This module contains the constant names for the various
MIDI controllers.

Having only the constants in this separate file permits to
call this from other programs, mainly the mma doc creators.

"""



""" English names for midi instruments and drums.

   These tables are used by the pattern classes to
   convert inst/drum names to midi values and by the
   doc routines to print tables.
"""

# The drum names are valid for tones 27 to 87

drumNames=[
    'HighQ', 'Slap', 'ScratchPush', 'ScratchPull',
    'Sticks', 'SquareClick', 'MetronomeClick',
    'MetronomeBell', 'KickDrum2', 'KickDrum1',
    'SideKick', 'SnareDrum1', 'HandClap',
    'SnareDrum2', 'LowTom2', 'ClosedHiHat',
    'LowTom1', 'PedalHiHat', 'MidTom2', 'OpenHiHat',
    'MidTom1', 'HighTom2', 'CrashCymbal1',
    'HighTom1', 'RideCymbal1', 'ChineseCymbal',
    'RideBell', 'Tambourine', 'SplashCymbal',
    'CowBell', 'CrashCymbal2', 'VibraSlap',
    'RideCymbal2', 'HighBongo', 'LowBongo',
    'MuteHighConga', 'OpenHighConga', 'LowConga',
    'HighTimbale', 'LowTimbale', 'HighAgogo',
    'LowAgogo', 'Cabasa', 'Maracas',
    'ShortHiWhistle', 'LongLowWhistle', 'ShortGuiro',
    'LongGuiro', 'Claves', 'HighWoodBlock',
    'LowWoodBlock', 'MuteCuica', 'OpenCuica',
    'MuteTriangle', 'OpenTriangle', 'Shaker',
    'JingleBell', 'Castanets', 'MuteSudro',
    'OpenSudro' ]

upperDrumNames = [name.upper() for name in drumNames]


voiceNames=[
    'Piano1', 'Piano2','Piano3',
    'Honky-TonkPiano', 'RhodesPiano', 'EPiano',
    'HarpsiChord', 'Clavinet', 'Celesta',
    'Glockenspiel', 'MusicBox', 'Vibraphone',
    'Marimba', 'Xylophone', 'TubularBells', 'Santur',
    'Organ1', 'Organ2', 'Organ3', 'ChurchOrgan',
    'ReedOrgan', 'Accordion', 'Harmonica',
    'Bandoneon', 'NylonGuitar', 'SteelGuitar',
    'JazzGuitar', 'CleanGuitar', 'MutedGuitar',
    'OverDriveGuitar', 'DistortonGuitar',
    'GuitarHarmonics', 'AcousticBass',
    'FingeredBass', 'PickedBass', 'FretlessBass',
    'SlapBass1', 'SlapBass2', 'SynthBass1',
    'SynthBass2', 'Violin', 'Viola', 'Cello',
    'ContraBass', 'TremoloStrings',
    'PizzicatoString', 'OrchestralHarp', 'Timpani',
    'Strings', 'SlowStrings', 'SynthStrings1',
    'SynthStrings2', 'ChoirAahs', 'VoiceOohs',
    'SynthVox', 'OrchestraHit', 'Trumpet',
    'Trombone', 'Tuba', 'MutedTrumpet', 'FrenchHorn',
    'BrassSection', 'SynthBrass1', 'SynthBrass2',
    'SopranoSax', 'AltoSax', 'TenorSax',
    'BaritoneSax', 'Oboe', 'EnglishHorn', 'Bassoon',
    'Clarinet', 'Piccolo', 'Flute', 'Recorder',
    'PanFlute', 'BottleBlow', 'Shakuhachi',
    'Whistle', 'Ocarina', 'SquareWave', 'SawWave',
    'SynCalliope', 'ChifferLead', 'Charang',
    'SoloVoice', '5thSawWave', 'Bass&Lead',
    'Fantasia', 'WarmPad', 'PolySynth', 'SpaceVoice',
    'BowedGlass', 'MetalPad', 'HaloPad', 'SweepPad',
    'IceRain', 'SoundTrack', 'Crystal', 'Atmosphere',
    'Brightness', 'Goblins', 'EchoDrops',
    'StarTheme', 'Sitar', 'Banjo', 'Shamisen',
    'Koto', 'Kalimba', 'BagPipe', 'Fiddle', 'Shanai',
    'TinkleBell', 'AgogoBells', 'SteelDrums',
    'WoodBlock', 'TaikoDrum', 'MelodicTom1',
    'SynthDrum', 'ReverseCymbal', 'GuitarFretNoise',
    'BreathNoise', 'SeaShore', 'BirdTweet',
    'TelephoneRing', 'HelicopterBlade',
    'Applause/Noise', 'GunShot' ]


upperVoiceNames = [name.upper() for name in voiceNames]

ctrlNames = [
    ### also see: http://www.midi.org/about-midi/table3.shtml

    ### 0-31 Double Precise Controllers
    ### MSB (14-bits, 16,384 values)

    'Bank', 'Modulation', 'Breath', 'Ctrl3',
    'Foot', 'Portamento', 'Data', 'Volume',
    'Balance', 'Ctrl9', 'Pan', 'Expression',
    'Effect1', 'Effect2', 'Ctrl14', 'Ctrl15',
    'General1','General2','General3','General4',
    'Ctrl20', 'Ctrl21', 'Ctrl22', 'Ctrl23',
    'Ctrl24', 'Ctrl25', 'Ctrl26', 'Ctrl27',
    'Ctrl28', 'Ctrl29', 'Ctrl30', 'Ctrl31',
    ### 32-63  Double Precise Controllers
    ### LSB (14-bits, 16,384 values)
    'BankLSB', 'ModulationLSB', 'BreathLSB',
    'Ctrl35', 'FootLSB', 'PortamentoLSB',
    'DataLSB','VolumeLSB','BalanceLSB',
    'Ctrl41','PanLSB','ExpressionLSB',
    'Effect1LSB', 'Effect2LSB','Ctrl46', 'Ctrl47',
    'General1LSB','General2LSB', 'General3LSB',
    'General4LSB', 'Ctrl52','Ctrl53', 'Ctrl54',
    'Ctrl55', 'Ctrl56', 'Ctrl57', 'Ctrl58',
    'Ctrl59', 'Ctrl60', 'Ctrl61', 'Ctrl62',
    'Ctrl63',

    ### 64-119 Single Precise Controllers
    ### (7-bits, 128 values)

    'Sustain', 'Portamento', 'Sostenuto',
    'SoftPedal', 'Legato', 'Hold2', 'Variation',
    'Resonance', 'ReleaseTime','AttackTime', 'Brightness',
    'DecayTime','VibratoRate','VibratoDepth', 'VibratoDelay',
    'Ctrl79','General5','General6','General7',
    'General8','PortamentoCtrl','Ctrl85','Ctrl86',
    'Ctrl87', 'Ctrl88', 'Ctrl89', 'Ctrl90',
    'Reverb', 'Tremolo', 'Chorus','Detune',
    'Phaser', 'DataInc','DataDec',
    'NonRegLSB', 'NonRegMSB',
    'RegParLSB', 'RegParMSB',
    'Ctrl102','Ctrl103','Ctrl104','Ctrl105',
    'Ctrl106','Ctrl107','Ctrl108','Ctrl109',
    'Ctrl110','Ctrl111','Ctrl112','Ctrl113',
    'Ctrl114','Ctrl115','Ctrl116','Ctrl117',
    'Ctrl118','Ctrl119',

    ### 120-127 Channel Mode Messages

    'AllSoundsOff','ResetAll',
    'LocalCtrl','AllNotesOff',
    'OmniOff','OmniOn', 'PolyOff','PolyOn' ]

upperCtrlNames = [name.upper() for name in ctrlNames]
