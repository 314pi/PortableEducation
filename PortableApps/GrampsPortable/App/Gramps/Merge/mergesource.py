#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2005  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
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
Provide merge capabilities for sources.
"""

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gen.lib import (Person, Family, Event, Place, Source, Repository,
                     MediaObject, Citation)
from gen.db import DbTxn
from gen.ggettext import sgettext as _
import const
import GrampsDisplay
import ManagedWindow
from Errors import MergeError

#-------------------------------------------------------------------------
#
# Gramps constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Entering_and_Editing_Data:_Detailed_-_part_3' % \
        const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Merge_Sources')
_GLADE_FILE = 'mergesource.glade'

#-------------------------------------------------------------------------
#
# Merge Sources
#
#-------------------------------------------------------------------------
class MergeSources(ManagedWindow.ManagedWindow):
    """
    Displays a dialog box that allows the sources to be combined into one.
    """
    def __init__(self, dbstate, uistate, handle1, handle2):
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.dbstate = dbstate
        database = dbstate.db
        self.src1 = database.get_source_from_handle(handle1)
        self.src2 = database.get_source_from_handle(handle2)

        self.define_glade('mergesource', _GLADE_FILE)
        self.set_window(self._gladeobj.toplevel,
                        self.get_widget('source_title'),
                        _("Merge Sources"))

        # Detailed Selection widgets
        title1 = self.src1.get_title()
        title2 = self.src2.get_title()
        entry1 = self.get_widget("title1")
        entry2 = self.get_widget("title2")
        entry1.set_text(title1)
        entry2.set_text(title2)
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('title1', 'title2', 'title_btn1', 'title_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        entry1 = self.get_widget("author1")
        entry2 = self.get_widget("author2")
        entry1.set_text(self.src1.get_author())
        entry2.set_text(self.src2.get_author())
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('author1', 'author2', 'author_btn1',
                    'author_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        entry1 = self.get_widget("abbrev1")
        entry2 = self.get_widget("abbrev2")
        entry1.set_text(self.src1.get_abbreviation())
        entry2.set_text(self.src2.get_abbreviation())
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('abbrev1', 'abbrev2', 'abbrev_btn1',
                    'abbrev_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        entry1 = self.get_widget("pub1")
        entry2 = self.get_widget("pub2")
        entry1.set_text(self.src1.get_publication_info())
        entry2.set_text(self.src2.get_publication_info())
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('pub1', 'pub2', 'pub_btn1', 'pub_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        gramps1 = self.src1.get_gramps_id()
        gramps2 = self.src2.get_gramps_id()
        entry1 = self.get_widget("gramps1")
        entry2 = self.get_widget("gramps2")
        entry1.set_text(gramps1)
        entry2.set_text(gramps2)
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('gramps1', 'gramps2', 'gramps_btn1',
                    'gramps_btn2'):
                self.get_widget(widget_name).set_sensitive(False)
        
        # Main window widgets that determine which handle survives
        rbutton1 = self.get_widget("handle_btn1")
        rbutton_label1 = self.get_widget("label_handle_btn1")
        rbutton_label2 = self.get_widget("label_handle_btn2")
        rbutton_label1.set_label(title1 + " [" + gramps1 + "]")
        rbutton_label2.set_label(title2 + " [" + gramps2 + "]")
        rbutton1.connect("toggled", self.on_handle1_toggled)

        self.connect_button('source_help', self.cb_help)
        self.connect_button('source_ok', self.cb_merge)
        self.connect_button('source_cancel', self.close)
        self.show()

    def on_handle1_toggled(self, obj):
        """first chosen source changes"""
        if obj.get_active():
            self.get_widget("title_btn1").set_active(True)
            self.get_widget("author_btn1").set_active(True)
            self.get_widget("abbrev_btn1").set_active(True)
            self.get_widget("pub_btn1").set_active(True)
            self.get_widget("gramps_btn1").set_active(True)
        else:
            self.get_widget("title_btn2").set_active(True)
            self.get_widget("author_btn2").set_active(True)
            self.get_widget("abbrev_btn2").set_active(True)
            self.get_widget("pub_btn2").set_active(True)
            self.get_widget("gramps_btn2").set_active(True)

    def cb_help(self, obj):
        """Display the relevant portion of Gramps manual"""
        GrampsDisplay.help(webpage = WIKI_HELP_PAGE, section = WIKI_HELP_SEC)

    def cb_merge(self, obj):
        """
        Performs the merge of the sources when the merge button is clicked.
        """
        self.uistate.set_busy_cursor(True)
        use_handle1 = self.get_widget("handle_btn1").get_active()
        if use_handle1:
            phoenix = self.src1
            titanic = self.src2
        else:
            phoenix = self.src2
            titanic = self.src1
            # Add second handle to history so that when merge is complete, 
            # phoenix is the selected row.
            self.uistate.set_active(phoenix.get_handle(), 'Source')

        if self.get_widget("title_btn1").get_active() ^ use_handle1:
            phoenix.set_title(titanic.get_title())
        if self.get_widget("author_btn1").get_active() ^ use_handle1:
            phoenix.set_author(titanic.get_author())
        if self.get_widget("abbrev_btn1").get_active() ^ use_handle1:
            phoenix.set_abbreviation(titanic.get_abbreviation())
        if self.get_widget("pub_btn1").get_active() ^ use_handle1:
            phoenix.set_publication_info(titanic.get_publication_info())
        if self.get_widget("gramps_btn1").get_active() ^ use_handle1:
            phoenix.set_gramps_id(titanic.get_gramps_id())

        query = MergeSourceQuery(self.dbstate, phoenix, titanic)
        query.execute()
        self.uistate.set_busy_cursor(False)
        self.close()

class MergeSourceQuery(object):
    """
    Create database query to merge two sources.
    """
    def __init__(self, dbstate, phoenix, titanic):
        self.database = dbstate.db
        self.phoenix = phoenix
        self.titanic = titanic

    def execute(self):
        """
        Merges to sources into a single source.
        """
        new_handle = self.phoenix.get_handle()
        old_handle = self.titanic.get_handle()

        self.phoenix.merge(self.titanic)

        with DbTxn(_("Merge Source"), self.database) as trans:
            self.database.commit_source(self.phoenix, trans)
            for (class_name, handle) in self.database.find_backlink_handles(
                    old_handle):
                if class_name == Citation.__name__:
                    citation = self.database.get_citation_from_handle(handle)
                    assert(citation.get_reference_handle() == old_handle)
                    citation.set_reference_handle(new_handle)
                    self.database.commit_citation(citation, trans)
                else:
                    raise MergeError("Encounter an object of type %s that has "
                            "a source reference." % class_name)
            self.database.remove_source(old_handle, trans)
