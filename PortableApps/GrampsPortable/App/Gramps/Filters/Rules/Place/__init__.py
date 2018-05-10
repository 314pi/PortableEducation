#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
# Copyright (C) 2007-2008  Brian G. Matherly
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
Package providing filter rules for GRAMPS.
"""

from _AllPlaces import AllPlaces
from _HasGallery import HasGallery
from _HasIdOf import HasIdOf
from _RegExpIdOf import RegExpIdOf
from _HasCitation import HasCitation
from _HasSourceOf import HasSourceOf
from _HasSourceCount import HasSourceCount
from _HasNote import HasNote
from _HasNoteRegexp import HasNoteRegexp
from _HasNoteMatchingSubstringOf import HasNoteMatchingSubstringOf
from _HasReferenceCountOf import HasReferenceCountOf
from _PlacePrivate import PlacePrivate
from _MatchesFilter import MatchesFilter
from _MatchesSourceConfidence import MatchesSourceConfidence
from _HasPlace import HasPlace
from _HasNoLatOrLon import HasNoLatOrLon
from _InLatLonNeighborhood import InLatLonNeighborhood
from _MatchesEventFilter import MatchesEventFilter
from _ChangedSince import ChangedSince

editor_rule_list = [
    AllPlaces,
    HasGallery,
    HasIdOf,
    RegExpIdOf,
    HasCitation,
    HasNote,
    HasNoteRegexp,
    HasReferenceCountOf,
    HasSourceOf,
    HasSourceCount,
    PlacePrivate,
    MatchesFilter,
    MatchesSourceConfidence,
    HasPlace,
    HasNoLatOrLon,
    InLatLonNeighborhood,
    MatchesEventFilter,
    ChangedSince,
]
