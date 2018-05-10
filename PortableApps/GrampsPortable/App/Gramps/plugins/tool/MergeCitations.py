#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
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

"""Tools/Family Tree Processing/MergeCitations"""

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".citation")

#-------------------------------------------------------------------------
#
# GNOME libraries
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Utils import confidence
import const
from gui.utils import ProgressMeter
from gui.plug import tool
from QuestionDialog import OkDialog
import GrampsDisplay
import DateHandler
import ManagedWindow
from gen.ggettext import sgettext as _
from gen.ggettext import ngettext
from glade import Glade
from gen.db import DbTxn
from gen.lib import (Person, Family, Event, Place, MediaObject, Citation, 
                     Repository)
from Errors import MergeError
from Merge import MergeCitationQuery

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
ALL_FIELDS = 0
IGNORE_DATE = 1
IGNORE_CONFIDENCE = 2
IGNORE_BOTH = 3

_val2label = {
    ALL_FIELDS        : _("Match on Page/Volume, Date and Confidence"),
    IGNORE_DATE       : _("Ignore Date"),
    IGNORE_CONFIDENCE : _("Ignore Confidence"),
    IGNORE_BOTH       : _("Ignore Date and Confidence")
    }

WIKI_HELP_PAGE = '%s_-_Tools' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Merge citations...')

#-------------------------------------------------------------------------
#
# The Actual tool.
#
#-------------------------------------------------------------------------
class MergeCitations(tool.BatchTool,ManagedWindow.ManagedWindow):
    
    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.dbstate = dbstate
        self.set_window(gtk.Window(), gtk.Label(), '')

        tool.BatchTool.__init__(self, dbstate, uistate, options_class, name)

        if not self.fail:
            uistate.set_busy_cursor(True)
            self.run()
            uistate.set_busy_cursor(False)
        
    def run(self):

        top = Glade(toplevel="mergecitations")

        # retrieve options
        fields = self.options.handler.options_dict['fields']
        dont_merge_notes = self.options.handler.options_dict['dont_merge_notes']

        my_menu = gtk.ListStore(str, object)
        for val in sorted(_val2label):
            my_menu.append([_val2label[val], val])

        self.notes_obj = top.get_object("notes")
        self.notes_obj.set_active(dont_merge_notes)
        self.notes_obj.show()
        
        self.menu = top.get_object("menu")
        self.menu.set_model(my_menu)
        self.menu.set_active(fields)

        window = top.toplevel
        window.show()
#        self.set_window(window, top.get_object('title'),
#                        _('Merge citations'))
        self.set_window(window, top.get_object('title2'),
                        _("Notes, media objects and data-items of matching "
                        "citations will be combined."))
        
        top.connect_signals({
            "on_merge_ok_clicked"   : self.on_merge_ok_clicked,
            "destroy_passed_object" : self.cancel,
            "on_help_clicked"       : self.on_help_clicked,
            "on_delete_merge_event" : self.close,
            "on_delete_event"       : self.close,
            })

        self.show()

    def cancel(self, obj):
        """
        on cancel, update the saved values of the options.
        """
        fields = self.menu.get_model()[self.menu.get_active()][1]
        dont_merge_notes = int(self.notes_obj.get_active())
        LOG.debug("cancel fields %d dont_merge_notes %d" % 
                  (fields, dont_merge_notes))

        self.options.handler.options_dict['fields'] = fields
        self.options.handler.options_dict['dont_merge_notes'] = dont_merge_notes
        # Save options
        self.options.handler.save_options()
        
        self.close(obj)
        
    def build_menu_names(self, obj):
        return (_("Tool settings"),_("Merge citations tool"))

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        
        GrampsDisplay.help(WIKI_HELP_PAGE , WIKI_HELP_SEC)

    def on_merge_ok_clicked(self, obj):
        """
        Performs the actual merge of citations
        (Derived from ExtractCity)
        """
        fields = self.menu.get_model()[self.menu.get_active()][1]
        dont_merge_notes = int(self.notes_obj.get_active())
        LOG.debug("fields %d dont_merge_notes %d" % (fields, dont_merge_notes))

        self.options.handler.options_dict['fields'] = fields
        self.options.handler.options_dict['dont_merge_notes'] = dont_merge_notes
        # Save options
        self.options.handler.save_options()

        self.progress = ProgressMeter(_('Checking Sources'), '')
        self.progress.set_pass(_('Looking for citation fields'), 
                               self.db.get_number_of_citations())

        db = self.dbstate.db
        
        db.disable_signals()
        num_merges = 0
        for handle in db.iter_source_handles():
            dict = {}
            citation_handle_list = list(db.find_backlink_handles(handle))
            for (class_name, citation_handle) in citation_handle_list:
                if class_name <> Citation.__name__:
                    raise MergeError("Encountered an object of type %s "
                    "that has a citation reference." % class_name)

                citation = db.get_citation_from_handle(citation_handle)
                key = citation.get_page()
                if fields <> IGNORE_DATE and fields <> IGNORE_BOTH:
                    key += "\n" + DateHandler.get_date(citation)
                if fields <> IGNORE_CONFIDENCE and fields <> IGNORE_BOTH:
                    key += "\n" + \
                        confidence[citation.get_confidence_level()]
                if key in dict and \
                    (not dont_merge_notes or len(citation.note_list) == 0):
                    citation_match_handle = dict[key]
                    citation_match = \
                        db.get_citation_from_handle(citation_match_handle)
                    try:
                        query = MergeCitationQuery(
                                self.dbstate, citation_match, citation)
                        query.execute()
                    except AssertionError:
                        print "Tool/Family Tree processing/MergeCitations", \
                        "citation1 gramps_id", citation_match.get_gramps_id(), \
                        "citation2 gramps_id", citation.get_gramps_id() , \
                        "citation backlink handles", \
                        list(db.find_backlink_handles(citation.get_handle()))
                    num_merges += 1
                elif (not dont_merge_notes or len(citation.note_list) == 0):
                    dict[key] = citation_handle
                self.progress.step()
        db.enable_signals()
        db.request_rebuild()
        self.progress.close()
        OkDialog(
            _("Number of merges done"),
            ngettext("%(num)d citation merged",
            "%(num)d citations merged", num_merges) % {'num': num_merges})
        self.close(obj)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class MergeCitationsOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        tool.ToolOptions.__init__(self, name,person_id)

        # Options specific for this report
        self.options_dict = {
            'fields'   : 1,
            'dont_merge_notes' : 0,
        }
        self.options_help = {
            'dont_merge_notes'   : 
                ("=0/1","Whether to merge citations if they have notes", 
                 ["Merge citations with notes", 
                  "Do not merge citations with notes"],
                 False),
            'fields' : ("=num","Threshold for matching",
                           "Integer number")
            }
