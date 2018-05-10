#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
# GTK libraries
#
#-------------------------------------------------------------------------
import gtk
import cgi

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import DateHandler
from gen.display.name import displayer as name_displayer
import Utils
import gen.lib
from gen.utils import get_birth_or_fallback, get_death_or_fallback

#-------------------------------------------------------------------------
#
# ChildModel
#
#-------------------------------------------------------------------------
class ChildModel(gtk.ListStore):

    def __init__(self, child_ref_list, db):
        gtk.ListStore.__init__(self, int, str, str, str, str, str, 
                               str, str, str, str, str, str, str, object)
        self.db = db
        for index, child_ref in enumerate(child_ref_list):
            child = db.get_person_from_handle(child_ref.ref)
            if child:
                self.append(row=[
                    index + 1, 
                    child.get_gramps_id(), 
                    name_displayer.display(child), 
                    Utils.gender[child.get_gender()], 
                    str(child_ref.get_father_relation()), 
                    str(child_ref.get_mother_relation()),
                    self.column_birth_day(child), 
                    self.column_death_day(child), 
                    self.column_birth_place(child), 
                    self.column_death_place(child), 
                    name_displayer.sort_string(child.primary_name), 
                    self.column_birth_sort(child), 
                    self.column_death_sort(child),
                    child_ref
                    ])

    def column_birth_day(self, data):
        birth = get_birth_or_fallback(self.db, data)
        if birth:
            if birth.get_type() == gen.lib.EventType.BIRTH:
                return DateHandler.get_date(birth)
            else:
                return '<i>%s</i>' % cgi.escape(DateHandler.get_date(birth))
        else:
            return u""

    def column_birth_sort(self, data):
        """ 
        Return a sort key to use for the birth column. 
        As python int can be larger than C int, we cast int 
        to a string of 10 long prepended with 0 as needed.
        This gives correct string sort for years in the millenia around today
        """
        birth = get_birth_or_fallback(self.db, data)
        if birth:
            return '%012d' % birth.get_date_object().get_sort_value()
        else:
            return '%012d' % 0

    def column_death_day(self, data):
        death = get_death_or_fallback(self.db, data)
        if death:
            if death.get_type() == gen.lib.EventType.DEATH:
                return DateHandler.get_date(death)
            else:
                return '<i>%s</i>' % cgi.escape(DateHandler.get_date(death))
        else:
            return u""

    def column_death_sort(self, data):
        """ 
        Return a sort key to use for the death column. 
        As python int can be larger than C int, we cast int 
        to a string of 10 long prepended with 0 as needed.
        This gives correct string sort for years in the millenia around today
        """
        death = get_death_or_fallback(self.db, data)
        if death:
            return '%012d' % death.get_date_object().get_sort_value()
        else:
            return '%012d' % 0
        
    def column_birth_place(self, data):
        event_ref = data.get_birth_ref()
        if event_ref and event_ref.ref:
            event = self.db.get_event_from_handle(event_ref.ref)
            if event:
                place_handle = event.get_place_handle()
                if place_handle:
                    return self.db.get_place_from_handle(place_handle).get_title()
        return u""

    def column_death_place(self, data):
        event_ref = data.get_death_ref()
        if event_ref and event_ref.ref:
            event = self.db.get_event_from_handle(event_ref.ref)
            if event:
                place_handle = event.get_place_handle()
                if place_handle:
                    return self.db.get_place_from_handle(place_handle).get_title()
        return u""
