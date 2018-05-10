#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
# Copyright (C) 2010       Nick Hall
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

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters.Rules._Rule import Rule
from gen.lib import Location

#-------------------------------------------------------------------------
#
# HasPlace
#
#-------------------------------------------------------------------------
class HasPlace(Rule):
    """Rule that checks for a place with a particular value"""


    labels      = [ _('Name:'), 
                    _('Street:'), 
                    _('Locality:'), 
                    _('City:'), 
                    _('County:'), 
                    _('State:'), 
                    _('Country:'), 
                    _('ZIP/Postal Code:'),
                    _('Church Parish:'), 
                    ]
    name        = _('Places matching parameters')
    description = _("Matches places with particular parameters")
    category    = _('General filters')
    allow_regex = True

    def apply(self, db, place):
        if not self.match_substring(0, place.get_title()):
            return False

        # If no location data was given then we're done: match
        if not any(self.list[1:]):
            return True
            
        # Something was given, so checking for location until we match
        for loc in [place.main_loc] + place.alt_loc:
            if self.apply_location(loc):
                return True

        # Nothing matched
        return False

    def apply_location(self, loc):
        if not loc:
            # Allow regular expressions to match empty fields
            loc = Location()

        if not self.match_substring(1, loc.get_street()):
            return False

        if not self.match_substring(2, loc.get_locality()):
            return False

        if not self.match_substring(3, loc.get_city()):
            return False

        if not self.match_substring(4, loc.get_county()):
            return False

        if not self.match_substring(5, loc.get_state()):
            return False

        if not self.match_substring(6, loc.get_country()):
            return False

        if not self.match_substring(7, loc.get_postal_code()):
            return False

        if not self.match_substring(8, loc.get_parish()):
            return False

        # Nothing contradicted, so we're matching this location
        return True
