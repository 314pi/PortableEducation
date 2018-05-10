#!/usr/bin/env python

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

import sys
import os

# Ensure a proper version is available.

pyMaj=2
pyMin=4

if sys.version_info[0] < pyMaj or sys.version_info[1] < pyMin:
	print
	print "You need a more current version of Python to run MMA."
	print "We're looking for something equal or greater than version %s.%s" % \
		  (pyMaj,pyMin)
	print "Current Python version is ", sys.version
	print
	sys.exit(0)

""" MMA uses a number of application specific modules. These should
    be installed in a mma modules directory or in your python
    site-packages directory). MMA searches for the modules
    directory and pre-pends the first found to the python system list.
"""

for d in ("c:\\mma", "/usr/local/share/mma", "/usr/share/mma", "."):
	if os.path.isdir(d):
		sys.path.insert(0, d)
		break;

# Call the mainline code. Hopefully, byte-compiled.

import MMA.main

