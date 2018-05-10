#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2008       B. Malengier
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
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

# Written by Alex Roitman

# $Id$

"""Tools/Utilities/Media Manager"""

#------------------------------------------------------------------------
#
# standard python modules
#
#------------------------------------------------------------------------
from __future__ import with_statement
import os

#------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#------------------------------------------------------------------------
import gtk
import gobject

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import const
import GrampsDisplay
import Assistant
import Errors
from gen.lib import MediaObject
from gen.db import DbTxn
from gen.updatecallback import UpdateCallback
from gui.plug import tool
from Utils import media_path_full, relative_path, media_path
from gen.ggettext import sgettext as _
import gen.mime

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Tools' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Media_Manager...')

#-------------------------------------------------------------------------
#
# This is an Assistant implementation to guide the user
#
#-------------------------------------------------------------------------
class MediaMan(tool.Tool):

    def __init__(self, dbstate, uistate, options_class, name, callback=None):

        tool.Tool.__init__(self, dbstate, options_class, name)
        self.uistate = uistate
        self.callback = uistate.pulse_progressbar

        self.build_batch_ops()
        self.batch_settings = None
        self.settings_page = None

        try:
            self.w = Assistant.Assistant(uistate,self.__class__,self.complete,
                                         _("Media Manager"))
        except Errors.WindowActiveError:
            return

        self.welcome_page = self.w.add_text_page(_('Gramps Media Manager'),
                                                 self.get_info_text())
        self.selection_page = self.w.add_page(_('Selecting operation'),
                                              self.build_selection_page())
        self.confirm_page = self.w.add_text_page('','')
        self.conclusion_page = self.w.add_text_page('','')

        self.w.connect('before-page-next',self.on_before_page_next)

        self.w.show()

    def complete(self):
        pass

    def on_before_page_next(self, obj,page,data=None):
        if page == self.selection_page:
            self.build_settings_page()
        elif page == self.settings_page:
            self.build_confirmation()
        elif page == self.confirm_page:
            success = self.run()
            self.build_conclusion(success)

    def get_info_text(self):
        return _("This tool allows batch operations on media objects "
                 "stored in Gramps. "
                 "An important distinction must be made between a Gramps "
                 "media object and its file.\n\n"
                 "The Gramps media object is a collection of data about "
                 "the media object file: its filename and/or path, its "
                 "description, its ID, notes, source references, etc. "
                 "These data <b>do not include the file itself</b>.\n\n"
                 "The files containing image, sound, video, etc, exist "
                 "separately on your hard drive. These files are "
                 "not managed by Gramps and are not included in the Gramps "
                 "database. "
                 "The Gramps database only stores the path and file names.\n\n"
                 "This tool allows you to only modify the records within "
                 "your Gramps database. If you want to move or rename "
                 "the files then you need to do it on your own, outside of "
                 "Gramps. Then you can adjust the paths using this tool so "
                 "that the media objects store the correct file locations.")

    def build_selection_page(self):
        """
        Build a page with the radio buttons for every available batch op.
        """
        self.batch_op_buttons = []

        box = gtk.VBox()
        box.set_spacing(12)

        table = gtk.Table(2*len(self.batch_ops),2)
        table.set_row_spacings(6)
        table.set_col_spacings(6)
        
        group = None
        for ix in range(len(self.batch_ops)):
            title = self.batch_ops[ix].title
            description= self.batch_ops[ix].description

            button = gtk.RadioButton(group,title)
            button.set_tooltip_text(description)
            if not group:
                group = button
            self.batch_op_buttons.append(button)
            table.attach(button,0,2,2*ix,2*ix+1,yoptions=0)
        
        box.add(table)
        return box

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help(webpage=WIKI_HELP_PAGE, section=WIKI_HELP_SEC)

    def build_batch_ops(self):
        self.batch_ops = []
        batches_to_use = [
            PathChange,
            Convert2Abs,
            Convert2Rel,
            ImagesNotIncluded,
            ]

        for batch_class in batches_to_use:
            self.batch_ops.append(batch_class(self.db,self.callback))

    def get_selected_op_index(self):
        """
        Query the selection radiobuttons and return the index number 
        of the selected batch op. 
        """
        for ix in range(len(self.batch_op_buttons)):
            button = self.batch_op_buttons[ix]
            if button.get_active():
                return ix
        else:
            return 0
    
    def build_settings_page(self):
        """
        Build an extra page with the settings specific for the chosen batch-op.
        If there's already an entry for this batch-op then do nothing,
        otherwise add a page.

        If the chosen batch-op does not have settings then remove the
        settings page that is already there (from previous user passes 
        through the assistant).
        """
        ix = self.get_selected_op_index()
        config = self.batch_ops[ix].build_config()
        if config:
            if ix == self.batch_settings:
                return
            elif self.batch_settings:
                self.w.remove_page(self.settings_page)
                self.settings_page = None
                self.confirm_page -= 1
                self.conclusion_page -= 1
                self.batch_settings = None
                self.build_confirmation()
            title,box = config
            self.settings_page = self.w.insert_page(title,box,
                                                    self.selection_page+1)
            self.confirm_page += 1
            self.conclusion_page += 1
            self.batch_settings = ix
            box.show_all()
        else:
            if self.batch_settings is not None:
                self.w.remove_page(self.settings_page)
                self.settings_page = None
                self.confirm_page -= 1
                self.conclusion_page -= 1
                self.batch_settings = None
            self.build_confirmation()

    def build_confirmation(self):
        """
        Build the confirmation page.

        This should query the selected settings and present the summary
        of the proposed action, as well as the list of affected paths.
        """

        ix = self.get_selected_op_index()
        confirm_text = self.batch_ops[ix].build_confirm_text()
        path_list = self.batch_ops[ix].build_path_list()

        box = gtk.VBox()
        box.set_spacing(12)
        box.set_border_width(12)

        label1 = gtk.Label(confirm_text)
        label1.set_line_wrap(True)
        label1.set_use_markup(True)
        label1.set_alignment(0,0.5)
        box.pack_start(label1,expand=False)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        tree = gtk.TreeView()
        model = gtk.ListStore(gobject.TYPE_STRING)
        tree.set_model(model)
        tree_view_column = gtk.TreeViewColumn(_('Affected path'),
                                              gtk.CellRendererText(),text=0)
        tree_view_column.set_sort_column_id(0)
        tree.append_column(tree_view_column)
        for path in path_list:
            model.append(row=[path])
        scrolled_window.add(tree)
        box.pack_start(scrolled_window,expand=True,fill=True)

        label3 = gtk.Label(_('Press OK to proceed, Cancel to abort, '
                             'or Back to revisit your options.'))
        box.pack_start(label3,expand=False)
        box.show_all()

        self.w.remove_page(self.confirm_page)
        self.confirm_page = self.w.insert_page(_('Final confirmation'),
                                               box,self.confirm_page)

    def run(self):
        """
        Run selected batch op with selected settings.
        """
        ix = self.get_selected_op_index()
        self.pre_run()
        success = self.batch_ops[ix].run_tool()
        self.post_run()
        return success
        
    def pre_run(self):
        self.uistate.set_busy_cursor(1)
        self.w.set_busy_cursor(1)
        self.uistate.progress.show()

    def post_run(self):
        self.uistate.set_busy_cursor(0)
        self.w.set_busy_cursor(0)
        self.uistate.progress.hide()

    def build_conclusion(self,success):
        if success:
            conclusion_title =  _('Operation successfully finished.')
            conclusion_text = _(
                'The operation you requested has finished successfully. '
                'You may press OK button now to continue.')
        else:
            conclusion_title =  _('Operation failed'),
            conclusion_text = _(
                'There was an error while performing the requested '
                'operation. You may try starting the tool again.')
        self.w.remove_page(self.conclusion_page)
        self.conclusion_page = self.w.insert_text_page(conclusion_title,
                                                       conclusion_text,
                                                       self.conclusion_page)

#------------------------------------------------------------------------
#
# These are the actuall sub-tools (batch-ops) for use from Assistant
#
#------------------------------------------------------------------------
class BatchOp(UpdateCallback):
    """
    Base class for the sub-tools.
    """
    title       = 'Untitled operation'
    description = 'This operation needs to be described'

    def __init__(self,db,callback):
        UpdateCallback.__init__(self,callback)
        self.db = db
        self.prepared = False

    def build_config(self):
        """
        This method should return either None (if the batch op requires
        no settings to run) or a tuple (title,box) for the settings page.
        """
        return None

    def build_confirm_text(self):
        """
        This method should return either None (if the batch op requires
        no confirmation) or a string with the confirmation text.
        """
        text = _(
            'The following action is to be performed:\n\n'
            'Operation:\t%s') % self.title.replace('_','')
        return text

    def build_path_list(self):
        """
        This method returns a list of the path names that would be
        affected by the batch op. Typically it would rely on prepare()
        to do the actual job, but it does not have to be that way.
        """
        self.prepare()
        return self.path_list

    def run_tool(self):
        """
        This method runs the batch op, taking care of database signals
        and transactions before and after the running.
        Should not be overridden without good reasons.
        """
        self.db.disable_signals()
        with DbTxn(self.title, self.db, batch=True) as self.trans:
            success = self._run()
        self.db.enable_signals()
        self.db.request_rebuild()
        return success

    def _run(self):
        """
        This method is the beef of the tool.
        Needs to be overridden in the subclass.
        """
        print "This method needs to be written."
        print "Running BatchOp tool... done."
        return True

    def prepare(self):
        """
        This method should prepare the tool for the actual run.
        Typically this involves going over media objects and
        selecting the ones that will be affected by the batch op.

        This method should set self.prepared to True, to indicate
        that it has already ran.
        """
        self.handle_list = []
        self.path_list = []
        self._prepare()
        self.prepared = True

    def _prepare(self):
        print "This method needs to be written."
        print "Preparing BatchOp tool... done."
        pass

#------------------------------------------------------------------------
# Simple op to replace substrings in the paths
#------------------------------------------------------------------------
class PathChange(BatchOp):
    title       = _('Replace _substrings in the path')
    description = _('This tool allows replacing specified substring in the '
                    'path of media objects with another substring. '
                    'This can be useful when you move your media files '
                    'from one directory to another')

    def build_config(self):
        title = _("Replace substring settings")

        box = gtk.VBox()
        box.set_spacing(12)

        table = gtk.Table(2,2)
        table.set_row_spacings(6)
        table.set_col_spacings(6)

        self.from_entry = gtk.Entry()
        table.attach(self.from_entry,1,2,0,1,yoptions=0)
        
        from_label = gtk.Label(_('_Replace:'))
        from_label.set_use_underline(True)
        from_label.set_alignment(0,0.5)
        from_label.set_mnemonic_widget(self.from_entry)
        table.attach(from_label,0,1,0,1,xoptions=0,yoptions=0)

        self.to_entry = gtk.Entry()
        table.attach(self.to_entry,1,2,1,2,yoptions=0)

        to_label = gtk.Label(_('_With:'))
        to_label.set_use_underline(True)
        to_label.set_alignment(0,0.5)
        to_label.set_mnemonic_widget(self.to_entry)
        table.attach(to_label,0,1,1,2,xoptions=0,yoptions=0)

        box.add(table)

        return (title,box)

    def build_confirm_text(self):
        from_text = unicode(self.from_entry.get_text())
        to_text = unicode(self.to_entry.get_text())
        text = _(
            'The following action is to be performed:\n\n'
            'Operation:\t%(title)s\nReplace:\t\t%(src_fname)s\nWith:\t\t%(dest_fname)s') % {
             'title' : self.title.replace('_',''), 'src_fname' : from_text, 'dest_fname' : to_text }
        return text
        
    def _prepare(self):
        from_text = unicode(self.from_entry.get_text())
        self.set_total(self.db.get_number_of_media_objects())
        with self.db.get_media_cursor() as cursor:
            for handle, data in cursor:
                obj = MediaObject()
                obj.unserialize(data)
                if obj.get_path().find(from_text) != -1:
                    self.handle_list.append(handle)
                    self.path_list.append(obj.path)
                self.update()
        self.reset()
        self.prepared = True

    def _run(self):
        if not self.prepared:
            self.prepare()
        self.set_total(len(self.handle_list))
        from_text = unicode(self.from_entry.get_text())
        to_text = unicode(self.to_entry.get_text())
        for handle in self.handle_list:
            obj = self.db.get_object_from_handle(handle)
            new_path = obj.get_path().replace(from_text,to_text)
            obj.set_path(new_path)
            self.db.commit_media_object(obj,self.trans)
            self.update()
        return True

#------------------------------------------------------------------------
#An op to convert relative paths to absolute
#------------------------------------------------------------------------
class Convert2Abs(BatchOp):
    title       = _('Convert paths from relative to _absolute')
    description = _("This tool allows converting relative media paths "
                    "to the absolute ones. It does this by prepending "
                    "the base path as given in the Preferences, or if "
                    "that is not set, it prepends user's directory.")

    def _prepare(self):
        self.set_total(self.db.get_number_of_media_objects())
        with self.db.get_media_cursor() as cursor:
            for handle, data in cursor:
                obj = MediaObject()
                obj.unserialize(data)
                if not os.path.isabs(obj.path):
                    self.handle_list.append(handle)
                    self.path_list.append(obj.path)
                self.update()
        self.reset()

    def _run(self):
        if not self.prepared:
            self.prepare()
        self.set_total(len(self.handle_list))
        for handle in self.handle_list:
            obj = self.db.get_object_from_handle(handle)
            new_path = media_path_full(self.db, obj.path)
            obj.set_path(new_path)
            self.db.commit_media_object(obj,self.trans)
            self.update()
        return True

#------------------------------------------------------------------------
#An op to convert absolute paths to relative
#------------------------------------------------------------------------
class Convert2Rel(BatchOp):
    title       = _('Convert paths from absolute to r_elative')
    description = _("This tool allows converting absolute media paths "
                    "to a relative path. The relative path is relative "
                    "viz-a-viz the base path as given in the Preferences, "
                    "or if that is not set, user's directory. "
                    "A relative path allows to tie the file location to "
                    "a base path that can change to your needs.")

    def _prepare(self):
        self.set_total(self.db.get_number_of_media_objects())
        with self.db.get_media_cursor() as cursor:
            for handle, data in cursor:
                obj = MediaObject()
                obj.unserialize(data)
                if os.path.isabs(obj.path):
                    self.handle_list.append(handle)
                    self.path_list.append(obj.path)
                self.update()
        self.reset()

    def _run(self):
        if not self.prepared:
            self.prepare()
        self.set_total(len(self.handle_list))
        base_dir = media_path(self.db)
        for handle in self.handle_list:
            obj = self.db.get_object_from_handle(handle)
            new_path = relative_path(obj.path, base_dir)
            obj.set_path(new_path)
            self.db.commit_media_object(obj,self.trans)
            self.update()
        return True

#------------------------------------------------------------------------
#An op to look for images that may have been forgotten.
#------------------------------------------------------------------------
class ImagesNotIncluded(BatchOp):
    title       = _('Add images not included in database')
    description = _("Check directories for images not included in database")
    description = _("This tool adds images in directories that are "
                    "referenced by existing images in the database.")

    def _prepare(self):
        """
        Get all of the fullpaths, and the directories of media
        objects in the database.
        """
        self.dir_list = set()
        self.set_total(self.db.get_number_of_media_objects())
        with self.db.get_media_cursor() as cursor:
            for handle, data in cursor:
                obj = MediaObject()
                obj.unserialize(data)
                self.handle_list.append(handle)
                full_path = media_path_full(self.db, obj.path)
                self.path_list.append(full_path)
                directory, filename = os.path.split(full_path)
                if directory not in self.dir_list:
                    self.dir_list.add(directory)
                self.update()
        self.reset()

    def build_path_list(self):
        """
        This method returns a list of the path names that would be
        affected by the batch op. Typically it would rely on prepare()
        to do the actual job, but it does not have to be that way.
        """
        self.prepare()
        return self.dir_list

    def _run(self):
        """
        Go through directories that are mentioned in the database via
        media files, and include all images that are not all ready
        included.
        """
        if not self.prepared:
            self.prepare()
        self.set_total(len(self.dir_list))
        for directory in self.dir_list:
            for (dirpath, dirnames, filenames) in os.walk(directory):
                if ".git" in dirnames:
                    dirnames.remove('.git')  # don't visit .git directories
                for filename in filenames:
                    media_full_path = os.path.join(dirpath, filename)
                    if media_full_path not in self.path_list:
                        self.path_list.append(media_full_path)
                        mime_type = gen.mime.get_type(media_full_path)
                        if gen.mime.is_image_type(mime_type):
                            obj = MediaObject()
                            obj.set_path(media_full_path)
                            obj.set_mime_type(mime_type)
                            (root, ext) = os.path.splitext(filename)
                            obj.set_description(root)
                            self.db.add_object(obj, self.trans)
            self.update()
        return True

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class MediaManOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        tool.ToolOptions.__init__(self, name,person_id)
