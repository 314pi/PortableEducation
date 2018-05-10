#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
# Copyright (C) 2007-2008   Brian G. Matherly
# Copyright (C) 2011       Tim G L Lyons
# Copyright (C) 2011       Doug Blank <doug.blank@gmail.com>
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

from _Disconnected import Disconnected
from _Everyone import Everyone
from _FamilyWithIncompleteEvent import FamilyWithIncompleteEvent
from _HasAddress import HasAddress
from _HasAlternateName import HasAlternateName
from _HasAssociation import HasAssociation
from _HasAttribute import HasAttribute
from _HasBirth import HasBirth
from _HasCitation import HasCitation
from _HasCommonAncestorWith import HasCommonAncestorWith
from _HasCommonAncestorWithFilterMatch import HasCommonAncestorWithFilterMatch
from _HasDeath import HasDeath
from _HasEvent import HasEvent
from _HasFamilyAttribute import HasFamilyAttribute
from _HasFamilyEvent import HasFamilyEvent
from _HasGallery import HavePhotos
from _HasIdOf import HasIdOf
from _HasLDS import HasLDS
from _HasNameOf import HasNameOf
from _HasNameOriginType import HasNameOriginType
from _HasNameType import HasNameType
from _HasNickname import HasNickname
from _HasNote import HasNote
from _HasNoteMatchingSubstringOf import HasNoteMatchingSubstringOf
from _HasNoteRegexp import HasNoteRegexp
from _HasRelationship import HasRelationship
from _HasSourceCount import HasSourceCount
from _HasSourceOf import HasSourceOf
from _HasTag import HasTag
from _HasTextMatchingRegexpOf import HasTextMatchingRegexpOf
from _HasTextMatchingSubstringOf import HasTextMatchingSubstringOf
from _HasUnknownGender import HasUnknownGender
from _HaveAltFamilies import HaveAltFamilies
from _HaveChildren import HaveChildren
from _IncompleteNames import IncompleteNames
from _IsAncestorOf import IsAncestorOf
from _IsAncestorOfFilterMatch import IsAncestorOfFilterMatch
from _IsBookmarked import IsBookmarked
from _IsChildOfFilterMatch import IsChildOfFilterMatch
from _IsDefaultPerson import IsDefaultPerson
from _IsDescendantFamilyOf import IsDescendantFamilyOf
from _IsDescendantOf import IsDescendantOf
from _IsDescendantOfFilterMatch import IsDescendantOfFilterMatch
from _IsDuplicatedAncestorOf import IsDuplicatedAncestorOf
from _IsFemale import IsFemale
from _IsLessThanNthGenerationAncestorOf import \
     IsLessThanNthGenerationAncestorOf
from _IsLessThanNthGenerationAncestorOfBookmarked import \
     IsLessThanNthGenerationAncestorOfBookmarked
from _IsLessThanNthGenerationAncestorOfDefaultPerson import \
     IsLessThanNthGenerationAncestorOfDefaultPerson
from _IsLessThanNthGenerationDescendantOf import \
     IsLessThanNthGenerationDescendantOf
from _IsMale import IsMale
from _IsMoreThanNthGenerationAncestorOf import \
     IsMoreThanNthGenerationAncestorOf
from _IsMoreThanNthGenerationDescendantOf import \
     IsMoreThanNthGenerationDescendantOf
from _IsParentOfFilterMatch import IsParentOfFilterMatch
from _IsSiblingOfFilterMatch import IsSiblingOfFilterMatch
from _IsSpouseOfFilterMatch import IsSpouseOfFilterMatch
from _IsWitness import IsWitness
from _MatchesFilter import MatchesFilter
from _MatchesEventFilter import MatchesEventFilter
from _MatchesSourceConfidence import MatchesSourceConfidence
from _MissingParent import MissingParent
from _MultipleMarriages import MultipleMarriages
from _NeverMarried import NeverMarried
from _NoBirthdate import NoBirthdate
from _NoDeathdate import NoDeathdate
from _PeoplePrivate import PeoplePrivate
from _PeoplePublic import PeoplePublic
from _PersonWithIncompleteEvent import PersonWithIncompleteEvent
from _ProbablyAlive import ProbablyAlive
from _RelationshipPathBetween import RelationshipPathBetween
from _DeepRelationshipPathBetween import DeepRelationshipPathBetween
from _RelationshipPathBetweenBookmarks import RelationshipPathBetweenBookmarks
from Filters.Rules._Rule import Rule
from _SearchName import SearchName
from _RegExpName import RegExpName
from _MatchIdOf import MatchIdOf
from _RegExpIdOf import RegExpIdOf
from _ChangedSince import ChangedSince
from _IsRelatedWith import IsRelatedWith

#-------------------------------------------------------------------------
#
# This is used by Custom Filter Editor tool
#
#-------------------------------------------------------------------------
editor_rule_list = [
    Everyone,
    IsFemale,
    HasUnknownGender,
    IsMale,
    IsDefaultPerson,
    IsBookmarked,
    HasAlternateName,
    HasAddress,
    HasAssociation,
    HasIdOf,
    HasLDS,
    HasNameOf,
    HasNameOriginType,
    HasNameType,
    HasNickname,
    HasRelationship,
    HasDeath,
    HasBirth,
    HasCitation, 
    HasEvent,
    HasFamilyEvent,
    HasAttribute,
    HasFamilyAttribute,
    HasTag,
    HasSourceCount,
    HasSourceOf,
    HaveAltFamilies,
    HavePhotos,
    HaveChildren,
    IncompleteNames,
    NeverMarried,
    MultipleMarriages,
    NoBirthdate,
    NoDeathdate,
    PersonWithIncompleteEvent,
    FamilyWithIncompleteEvent,
    ProbablyAlive,
    PeoplePrivate,
    PeoplePublic,
    IsWitness,
    IsDescendantOf,
    IsDescendantFamilyOf,
    IsLessThanNthGenerationAncestorOfDefaultPerson,
    IsDescendantOfFilterMatch,
    IsDuplicatedAncestorOf,
    IsLessThanNthGenerationDescendantOf,
    IsMoreThanNthGenerationDescendantOf,
    IsAncestorOf,
    IsAncestorOfFilterMatch,
    IsLessThanNthGenerationAncestorOf,
    IsLessThanNthGenerationAncestorOfBookmarked,
    IsMoreThanNthGenerationAncestorOf,
    HasCommonAncestorWith,
    HasCommonAncestorWithFilterMatch,
    MatchesFilter,
    MatchesEventFilter,
    MatchesSourceConfidence,
    MissingParent,
    IsChildOfFilterMatch,
    IsParentOfFilterMatch,
    IsSpouseOfFilterMatch,
    IsSiblingOfFilterMatch,
    RelationshipPathBetween,
    DeepRelationshipPathBetween,
    RelationshipPathBetweenBookmarks,
    HasTextMatchingSubstringOf,
    HasNote,
    HasNoteRegexp,
    RegExpIdOf,
    Disconnected,
    ChangedSince,
    IsRelatedWith,
]

