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
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# gtk
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gui import widgets
from Filters.SideBar import SidebarFilter
from Filters import GenericFilterFactory, build_filter_model, Rules
from Filters.Rules.Source import (RegExpIdOf, HasSource, HasNoteRegexp, 
                                  MatchesFilter)

GenericSourceFilter = GenericFilterFactory('Source')
#-------------------------------------------------------------------------
#
# PersonSidebarFilter class
#
#-------------------------------------------------------------------------
class SourceSidebarFilter(SidebarFilter):

    def __init__(self, dbstate, uistate, clicked):
        self.clicked_func = clicked
        self.filter_id = widgets.BasicEntry()
        self.filter_title = widgets.BasicEntry()
        self.filter_author = widgets.BasicEntry()
        self.filter_abbr = widgets.BasicEntry()
        self.filter_pub = widgets.BasicEntry()
        self.filter_note = widgets.BasicEntry()

        self.filter_regex = gtk.CheckButton(_('Use regular expressions'))

        self.generic = gtk.ComboBox()

        SidebarFilter.__init__(self, dbstate, uistate, "Source")

    def create_widget(self):
        cell = gtk.CellRendererText()
        cell.set_property('width', self._FILTER_WIDTH)
        cell.set_property('ellipsize', self._FILTER_ELLIPSIZE)
        self.generic.pack_start(cell, True)
        self.generic.add_attribute(cell, 'text', 0)
        self.on_filters_changed('Source')

        self.add_text_entry(_('ID'), self.filter_id)
        self.add_text_entry(_('Title'), self.filter_title)
        self.add_text_entry(_('Author'), self.filter_author)
        self.add_text_entry(_('Abbreviation'), self.filter_abbr)
        self.add_text_entry(_('Publication'), self.filter_pub)
        self.add_text_entry(_('Note'), self.filter_note)
        self.add_filter_entry(_('Custom filter'), self.generic)
        self.add_regex_entry(self.filter_regex)

    def clear(self, obj):
        self.filter_id.set_text('')
        self.filter_title.set_text('')
        self.filter_author.set_text('')
        self.filter_abbr.set_text('')
        self.filter_pub.set_text('')
        self.filter_note.set_text('')
        self.generic.set_active(0)

    def get_filter(self):
        gid = unicode(self.filter_id.get_text()).strip()
        title = unicode(self.filter_title.get_text()).strip()
        author = unicode(self.filter_author.get_text()).strip()
        abbr = unicode(self.filter_abbr.get_text()).strip()
        pub = unicode(self.filter_pub.get_text()).strip()
        note = unicode(self.filter_note.get_text()).strip()
        regex = self.filter_regex.get_active()
        gen = self.generic.get_active() > 0

        empty = not (gid or title or author or abbr or pub or note or regex or
                     gen)
        if empty:
            generic_filter = None
        else:
            generic_filter = GenericSourceFilter()
            if gid:
                rule = RegExpIdOf([gid], use_regex=regex)
                generic_filter.add_rule(rule)

            rule = HasSource([title, author, abbr, pub], use_regex=regex)
            generic_filter.add_rule(rule)
                
            if note:
                rule = HasNoteRegexp([note], use_regex=regex)
                generic_filter.add_rule(rule)

        if self.generic.get_active() != 0:
            model = self.generic.get_model()
            node = self.generic.get_active_iter()
            obj = unicode(model.get_value(node, 0))
            rule = MatchesFilter([obj])
            generic_filter.add_rule(rule)

        return generic_filter

    def on_filters_changed(self, name_space):
        if name_space == 'Source':
            all_filter = GenericSourceFilter()
            all_filter.set_name(_("None"))
            all_filter.add_rule(Rules.Source.AllSources([]))
            self.generic.set_model(build_filter_model('Source', [all_filter]))
            self.generic.set_active(0)
