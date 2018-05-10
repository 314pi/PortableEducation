#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
from Filters.Rules import Rule
from Utils import get_participant_from_event

#-------------------------------------------------------------------------
#
# HasEventBase
#
#-------------------------------------------------------------------------
class HasEventBase(Rule):
    """Rule that checks for an event with a particular value."""


    labels      = [ _('Event type:'), 
                    _('Date:'), 
                    _('Place:'), 
                    _('Description:'),
                    _('Main Participants:') ]
    name        =  _('Events matching parameters')
    description =  _("Matches events with particular parameters")
    category    = _('Event filters')
    allow_regex = True
    
    def prepare(self, db):
        self.date = None
        if self.list[0]:
            self.etype = EventType()
            self.etype.set_from_xml_str(self.list[0])
        else:
            self.etype = None
        try:
            if self.list[1]:
                self.date = DateHandler.parser.parse(self.list[1])
        except:
            pass

    def apply(self, db, event):
        if self.etype:
            if self.etype.is_custom() and self.use_regex:
                if self.regex[0].search(str(event.type)) is None:
                    return False
            elif event.type != self.etype:
                return False

        if not self.match_substring(3, event.get_description()):
            return False

        if self.date:
            if not event.get_date_object().match(self.date):
                return False

        if self.list[2]:
            place_id = event.get_place_handle()
            if place_id:
                place = db.get_place_from_handle(place_id)
                place_name = place.get_title()
                if not self.match_substring(2, place_name):
                    return False
            else:
                return False

        if not self.match_substring(4,
                get_participant_from_event(db, event.get_handle(), all_=True)):
            return False

        return True
