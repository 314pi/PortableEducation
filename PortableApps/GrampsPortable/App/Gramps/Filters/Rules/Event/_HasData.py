#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008  Gary Burton
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
import DateHandler
from gen.lib import EventType
from Filters.Rules._Rule import Rule

#-------------------------------------------------------------------------
#
# HasBirth
#
#-------------------------------------------------------------------------
class HasData(Rule):
    """Rule that checks for an event containing particular values"""

    labels      = [ _('Event type:'), _('Date:'), _('Place:'),
                    _('Description:') ]
    name        = _('Events with <data>')
    description = _("Matches events with data of a particular value")
    category    = _('General filters')
    allow_regex = True
    
    def prepare(self, dbase):
        self.event_type = self.list[0]
        self.date = self.list[1]

        if self.event_type:
            self.event_type = EventType()
            self.event_type.set_from_xml_str(self.list[0])

        if self.date:
            self.date = DateHandler.parser.parse(self.date)
        
    def apply(self, db, event):
        if self.event_type and event.get_type() != self.event_type:
            # No match
            return False

        if self.date and not event.get_date_object().match(self.date):
            # No match
            return False

        if self.list[2]:
            place_id = event.get_place_handle()
            if place_id:
                place = db.get_place_from_handle(place_id)
                if not self.match_substring(2, place.get_title()):
                    # No match
                    return False
            else:
                # No place attached to event
                return False

        if not self.match_substring(3, event.get_description()):
            # No match
            return False

        # All conditions matched
        return True
