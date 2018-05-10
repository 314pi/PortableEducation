#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004-2007  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""
Class handling language-specific selection for date parser and displayer.
"""
#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging

# import prerequisites for localized handlers
from _DateHandler import (LANG, LANG_SHORT, LANG_TO_PARSER, LANG_TO_DISPLAY, 
                          register_datehandler)
                          
from gen.ggettext import gettext as _

# Import all the localized handlers
import _Date_ar
import _Date_bg
import _Date_ca
import _Date_cs
import _Date_da
import _Date_de
import _Date_el
import _Date_es
import _Date_fi
import _Date_fr
import _Date_hr
import _Date_it
import _Date_lt
import _Date_nb
import _Date_nl
import _Date_pl
import _Date_pt
import _Date_ru
import _Date_sk
import _Date_sl
import _Date_sr
import _Date_sv
import _Date_uk

# Initialize global parser
try:
    if LANG in LANG_TO_PARSER:
        parser = LANG_TO_PARSER[LANG]()
    else:
        parser = LANG_TO_PARSER[LANG_SHORT]()
except:
    logging.warning(_("Date parser for '%s' not available, using default") % LANG)
    parser = LANG_TO_PARSER["C"]()

# Initialize global displayer
try:
    import config
    val = config.get('preferences.date-format')
except:
    val = 0

try:
    if LANG in LANG_TO_DISPLAY:
        displayer = LANG_TO_DISPLAY[LANG](val)
    else:
        displayer = LANG_TO_DISPLAY[LANG_SHORT](val)
except:
    logging.warning(_("Date displayer for '%s' not available, using default") % LANG)
    displayer = LANG_TO_DISPLAY["C"](val)


# Import utility functions
from _DateUtils import *
