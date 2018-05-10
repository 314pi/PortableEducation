#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011  Jerome Rapinat
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
# Filters/Rules/Event/_MatchesSourceConfidence.py
# $Id$
#

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters.Rules._MatchesSourceConfidenceBase import MatchesSourceConfidenceBase

#-------------------------------------------------------------------------
# "Confidence level"
# Sources of an attribute of an event are ignored
#-------------------------------------------------------------------------
class MatchesSourceConfidence(MatchesSourceConfidenceBase):
    """Events matching a specific confidence level on its 'direct' source references"""

    labels    = [_('Confidence level:')]
    name        = _('Events with at least one direct source >= <confidence level>')
    description = _("Matches events with at least one direct source with confidence level(s)")

