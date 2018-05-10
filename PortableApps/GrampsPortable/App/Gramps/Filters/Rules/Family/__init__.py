#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
# Copyright (C) 2007-2008  Brian G. Matherly
# Copyright (C) 2011       Tim G L Lyons
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

from _SearchFatherName import SearchFatherName
from _SearchMotherName import SearchMotherName
from _SearchChildName import SearchChildName
from _RegExpFatherName import RegExpFatherName
from _RegExpMotherName import RegExpMotherName
from _RegExpChildName import RegExpChildName

from _HasRelType import HasRelType
from _AllFamilies import AllFamilies
from _HasGallery import HasGallery
from _HasIdOf import HasIdOf
from _HasLDS import HasLDS
from _RegExpIdOf import RegExpIdOf
from _HasNote import HasNote
from _HasNoteRegexp import HasNoteRegexp
from _HasNoteMatchingSubstringOf import HasNoteMatchingSubstringOf
from _HasSourceCount import HasSourceCount
from _HasReferenceCountOf import HasReferenceCountOf
from _HasCitation import HasCitation
from _FamilyPrivate import FamilyPrivate
from _HasAttribute import HasAttribute
from _HasEvent import HasEvent
from _HasSourceOf import HasSourceOf
from _IsBookmarked import IsBookmarked
from _MatchesFilter import MatchesFilter
from _MatchesSourceConfidence import MatchesSourceConfidence
from _FatherHasNameOf import FatherHasNameOf
from _FatherHasIdOf import FatherHasIdOf
from _MotherHasNameOf import MotherHasNameOf
from _MotherHasIdOf import MotherHasIdOf
from _ChildHasNameOf import ChildHasNameOf
from _ChildHasIdOf import ChildHasIdOf
from _ChangedSince import ChangedSince
from _HasTag import HasTag

editor_rule_list = [
    AllFamilies,
    HasRelType,
    HasGallery,
    HasIdOf,
    HasLDS,
    HasNote,
    RegExpIdOf,
    HasNoteRegexp,
    HasReferenceCountOf,
    HasSourceCount,
    HasSourceOf,
    HasCitation, 
    FamilyPrivate,
    HasEvent,
    HasAttribute,
    IsBookmarked,
    MatchesFilter,
    MatchesSourceConfidence,
    FatherHasNameOf,
    FatherHasIdOf,
    MotherHasNameOf,
    MotherHasIdOf,
    ChildHasNameOf,
    ChildHasIdOf,
    ChangedSince,
    HasTag,
]
