#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Brian G. Matherly
# Copyright (C) 2009       Gary Burton
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
Provide the management of databases. This includes opening, renaming,
creating, and deleting of databases.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import time
import copy
import subprocess
import urlparse
from gen.ggettext import gettext as _
#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".DbManager")

import constfunc
if constfunc.win():
    _RCS_FOUND = os.system("rcs -V >nul 2>nul") == 0
    if _RCS_FOUND and "TZ" not in os.environ:
        # RCS requires the "TZ" variable be set.
        os.environ["TZ"] = str(time.timezone)
else:
    _RCS_FOUND = os.system("rcs -V >/dev/null 2>/dev/null") == 0

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
from gtk.gdk import ACTION_COPY
import pango

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from QuestionDialog import ErrorDialog, QuestionDialog, QuestionDialog2
from gen.db import DbBsddb
from gui.pluginmanager import GuiPluginManager
from cli.clidbman import CLIDbManager, NAME_FILE, time_val
from DdTargets import DdTargets
import RecentFiles
from glade import Glade
from gen.db.backup import restore
from gen.db.exceptions import DbException
from Utils import get_unicode_path_from_env_var


_RETURN = gtk.gdk.keyval_from_name("Return")
_KP_ENTER = gtk.gdk.keyval_from_name("KP_Enter")


#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------

ARCHIVE       = "rev.gramps"
ARCHIVE_V     = "rev.gramps,v"

NAME_COL  = 0
PATH_COL  = 1
FILE_COL  = 2
DATE_COL  = 3
DSORT_COL = 4
OPEN_COL  = 5
STOCK_COL = 6

RCS_BUTTON = { True : _('_Extract'), False : _('_Archive') }

class DbManager(CLIDbManager):
    """
    Database Manager. Opens a database manager window that allows users to
    create, rename, delete and open databases.
    """
    ICON_MAP = {
                CLIDbManager.ICON_NONE : '',
                CLIDbManager.ICON_RECOVERY : gtk.STOCK_DIALOG_ERROR,
                CLIDbManager.ICON_LOCK : 'gramps-lock',
                CLIDbManager.ICON_OPEN : gtk.STOCK_OPEN,
               }

    ERROR = ErrorDialog
        
    def __init__(self, dbstate, parent=None):
        """
        Create the top level window from the glade description, and extracts
        the GTK widgets that are needed.
        """
        CLIDbManager.__init__(self, dbstate)
        self.glade = Glade()
        self.top = self.glade.toplevel

        if parent:
            self.top.set_transient_for(parent)

        for attr in ['connect', 'cancel', 'new', 'remove',
                     'dblist', 'rename', 'repair', 'rcs', 'msg']:
            setattr(self, attr, self.glade.get_object(attr))

        self.model = None
        self.column  = None
        self.lock_file = None
        self.data_to_delete = None

        self.selection = self.dblist.get_selection()
        self.dblist.set_rules_hint(True)

        self.__connect_signals()
        self.__build_interface()
        self._populate_model()

    def __connect_signals(self):
        """
        Connects the signals to the buttons on the interface. 
        """
        ddtargets = [ DdTargets.URI_LIST.target() ]
        self.top.drag_dest_set(gtk.DEST_DEFAULT_ALL, ddtargets, ACTION_COPY)

        self.remove.connect('clicked', self.__remove_db)
        self.new.connect('clicked', self.__new_db)
        self.rename.connect('clicked', self.__rename_db)
        self.repair.connect('clicked', self.__repair_db)
        self.selection.connect('changed', self.__selection_changed)
        self.dblist.connect('button-press-event', self.__button_press)
        self.dblist.connect('key-press-event', self.__key_press)
        self.top.connect('drag_data_received', self.__drag_data_received)
        self.top.connect('drag_motion', drag_motion)
        self.top.connect('drag_drop', drop_cb)

        if _RCS_FOUND:
            self.rcs.connect('clicked', self.__rcs)

    def __button_press(self, obj, event):
        """
        Checks for a double click event. In the tree view, we want to 
        treat a double click as if it was OK button press. However, we have
        to make sure that an item was selected first.
        """
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            if self.connect.get_property('sensitive'):
                self.top.response(gtk.RESPONSE_OK)
                return True
        return False

    def __key_press(self, obj, event):
        """
        Grab ENTER so it does not start editing the cell, but behaves
        like double click instead
        """
        if event.keyval in (_RETURN, _KP_ENTER):
            if self.connect.get_property('sensitive'):
                self.top.response(gtk.RESPONSE_OK)
                return True
        return False

    def __selection_changed(self, selection):
        """
        Called when the selection is changed in the TreeView. 
        """
        self.__update_buttons(selection)

    def __update_buttons(self, selection):
        """
        What we are trying to detect is the selection or unselection of a row.
        When a row is unselected, the Open, Rename, and Remove buttons
        are set insensitive. If a row is selected, the rename and remove
        buttons are disabled, and the Open button is disabled if the
        row represents a open database.
        """
            
        # Get the current selection
        store, node = selection.get_selected()
        
        # if nothing is selected
        if not node:
            self.connect.set_sensitive(False)
            self.rename.set_sensitive(False)
            self.rcs.set_sensitive(False)
            self.repair.set_sensitive(False)
            self.remove.set_sensitive(False)
            return
        
        path = self.model.get_path(node)
        if path is None:
            return

        is_rev = len(path) > 1
        self.rcs.set_label(RCS_BUTTON[is_rev])

        if store.get_value(node, STOCK_COL) == gtk.STOCK_OPEN:
            self.connect.set_sensitive(False)
            if _RCS_FOUND:
                self.rcs.set_sensitive(True)
        else:
            self.connect.set_sensitive(not is_rev)
            if _RCS_FOUND and is_rev:
                self.rcs.set_sensitive(True)
            else:
                self.rcs.set_sensitive(False)

        if store.get_value(node, STOCK_COL) == gtk.STOCK_DIALOG_ERROR:
            path = get_unicode_path_from_env_var(store.get_value(node, PATH_COL))
            backup = os.path.join(path, "person.gbkp")
            self.repair.set_sensitive(os.path.isfile(backup))
        else:
            self.repair.set_sensitive(False)
            
        self.rename.set_sensitive(True)
        self.remove.set_sensitive(True)

    def __build_interface(self):
        """
        Builds the columns for the TreeView. The columns are:

        Icon, Database Name, Last Modified

        The Icon column gets its data from column 6 of the database model.
        It is expecting either None, or a GTK stock icon name

        The Database Name column is an editable column. We connect to the
        'edited' signal, so that we can change the name when the user changes
        the column.

        The last accessed column simply displays the last time famtree was 
        opened.
        """

        # build the database name column
        render = gtk.CellRendererText()
        render.set_property('ellipsize', pango.ELLIPSIZE_END)
        render.connect('edited', self.__change_name)
        render.connect('editing-canceled', self.__stop_edit)
        render.connect('editing-started', self.__start_edit)
        self.column = gtk.TreeViewColumn(_('Family tree name'), render, 
                                         text=NAME_COL)
        self.column.set_sort_column_id(NAME_COL)
        self.column.set_resizable(True)
        self.column.set_min_width(275)
        self.dblist.append_column(self.column)
        self.name_renderer = render

        # build the icon column
        render = gtk.CellRendererPixbuf()
        icon_column = gtk.TreeViewColumn(_('Status'), render, 
                                         stock_id=STOCK_COL)
        self.dblist.append_column(icon_column)

        # build the last accessed column
        render = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Last accessed'), render, text=DATE_COL)
        column.set_sort_column_id(DSORT_COL)
        self.dblist.append_column(column)

        # set the rules hit
        self.dblist.set_rules_hint(True)

    def __populate(self):
        """
        Builds the data and the display model.
        """
        self._populate_cli()
        self._populate_model()
        
    def _populate_model(self):
        """
        Builds the display model.
        """
        self.model = gtk.TreeStore(str, str, str, str, int, bool, str)

        #use current names to set up the model
        for items in self.current_names:
            data = list(items[:7])
            node = self.model.append(None, data)
            for rdata in find_revisions(os.path.join(items[1], ARCHIVE_V)):
                data = [ rdata[2], rdata[0], items[1], rdata[1], 0, False, "" ]
                self.model.append(node, data)
        self.dblist.set_model(self.model)

    def existing_name(self, name, skippath=None):
        """
        Return true if a name is present in the model already.
        If skippath given, the name of skippath is not considered
        """
        iter = self.model.get_iter_first()
        while (iter):
            path = self.model.get_path(iter)
            if path == skippath:
                continue
            itername = self.model.get_value(iter, NAME_COL)
            if itername.strip() == name.strip():
                return True
            iter = self.model.iter_next(iter)
        return False

    def run(self):
        """
        Runs the dialog, returning None if nothing has been chosen,
        or the path and name if something has been selected
        """
        while True:
            value = self.top.run()
            if value == gtk.RESPONSE_OK:
                store, node = self.selection.get_selected()
                # don't open a locked file
                if store.get_value(node, STOCK_COL) == 'gramps-lock':
                    self.__ask_to_break_lock(store, node)
                    continue 
                # don't open a version
                if len(store.get_path(node)) > 1:
                    continue
                if node:
                    self.top.destroy()
                    del self.selection
                    del self.name_renderer
                    path = get_unicode_path_from_env_var(store.get_value(node, PATH_COL))
                    return (path, store.get_value(node, NAME_COL))
            else:
                self.top.destroy()
                del self.selection
                del self.name_renderer
                return None

    def __ask_to_break_lock(self, store, node):
        """
        Prompts the user for permission to break the lock file that another
        process has set on the file.
        """
        path = store.get_path(node)
        self.lock_file = store[path][PATH_COL]

        QuestionDialog(
            _("Break the lock on the '%s' database?") % store[path][0],
            _("Gramps believes that someone else is actively editing "
              "this database. You cannot edit this database while it "
              "is locked. If no one is editing the database you may "
              "safely break the lock. However, if someone else is editing "
              "the database and you break the lock, you may corrupt the "
              "database."),
            _("Break lock"),
            self.__really_break_lock)

    def __really_break_lock(self):
        """
        Deletes the lock file associated with the selected database, then updates
        the display appropriately.
        """
        try:
            self.break_lock(self.lock_file)
            store, node = self.selection.get_selected()
            dbpath = get_unicode_path_from_env_var(store.get_value(node, PATH_COL))
            (tval, last) = time_val(dbpath)
            store.set_value(node, OPEN_COL, 0)
            store.set_value(node, STOCK_COL, "")
            store.set_value(node, DATE_COL, last)
            store.set_value(node, DSORT_COL, tval)
        except IOError:
            return

    def __stop_edit(self, *args):
        self.name_renderer.set_property('editable', False)
        self.__update_buttons(self.selection)

    def __start_edit(self, *args):
        """
        Do no allow to click Load while changing name, to force users to finish
        the action of renaming. Hack around the fact that clicking button
        sends a 'editing-canceled' signal loosing the new name
        """
        self.connect.set_sensitive(False)
        self.rename.set_sensitive(False)

    def __change_name(self, renderer_sel, path, new_text):
        """
        Change the name of the database. This is a callback from the
        column, which has been marked as editable. 

        If the new string is empty, do nothing. Otherwise, renaming the	
        database is simply changing the contents of the name file.
        """
        if len(new_text) > 0:
            node = self.model.get_iter(path)
            old_text = self.model.get_value(node, NAME_COL)
            if not old_text.strip() == new_text.strip():
                #If there is a ":" in path, then it as revision
                if ":" in path :
                    self.__rename_revision(path, new_text)
                else:
                    self.__rename_database(path, new_text)
        
        self.name_renderer.set_property('editable', False)
        self.__update_buttons(self.selection)

    def __rename_revision(self, path, new_text):
        """
        Renames the RCS revision using the rcs command. The rcs command 
        is in the format of:

           rcs -mREV:NEW_NAME archive

        """
        node = self.model.get_iter(path)
        db_dir = self.model.get_value(node, FILE_COL)
        rev = self.model.get_value(node, PATH_COL)
        archive = os.path.join(db_dir, ARCHIVE_V)

        cmd = [ "rcs", "-x,v", "-m%s:%s" % (rev, new_text), archive ]

        proc = subprocess.Popen(cmd, stderr = subprocess.PIPE)
        status = proc.wait()
        message = "\n".join(proc.stderr.readlines())
        proc.stderr.close()
        del proc

        if status != 0:
            DbManager.ERROR(
                _("Rename failed"),
                _("An attempt to rename a version failed "
                  "with the following message:\n\n%s") % message
                )
        else:
            self.model.set_value(node, NAME_COL, new_text)

    def __rename_database(self, path, new_text):
        """
        Renames the database by writing the new value to the name.txt file
        """
        new_text = new_text.strip()
        node = self.model.get_iter(path)
        filename = self.model.get_value(node, FILE_COL)
        if self.existing_name(new_text, skippath=path):
            DbManager.ERROR(_("Could not rename the Family Tree."), 
                  _("Family Tree already exists, choose a unique name."))
            return
        old_text, new_text = self.rename_database(filename, new_text)
        if not (old_text is None):
            RecentFiles.rename_filename(old_text, new_text)
            self.model.set_value(node, NAME_COL, new_text)

    def __rcs(self, obj):
        """
        Callback for the RCS button. If the tree path is > 1, then we are
        on an RCS revision, in which case we can check out. If not, then
        we can only check in.
        """
        store, node = self.selection.get_selected()
        tree_path = store.get_path(node)
        if len(tree_path) > 1:
            parent_node = store.get_iter((tree_path[0],))
            parent_name = store.get_value(parent_node, NAME_COL)
            name = store.get_value(node, NAME_COL)
            revision = store.get_value(node, PATH_COL)
            db_path = store.get_value(node, FILE_COL)

            self.__checkout_copy(parent_name, name, revision, db_path)
        else:
            base_path = self.dbstate.db.get_save_path()
            archive = os.path.join(base_path, ARCHIVE) 
            check_in(self.dbstate.db, archive, None, self.__start_cursor)
            self.__end_cursor()

        self.__populate()
        
    def __checkout_copy(self, parent_name, name, revision, db_path):
        """
        Create a new database, then extracts a revision from RCS and
        imports it into the db
        """
        new_path, newname = self._create_new_db("%s : %s" % (parent_name, name))
        
        self.__start_cursor(_("Extracting archive..."))
        dbclass = DbBsddb
        dbase = dbclass()
        dbase.load(new_path, None)
        
        self.__start_cursor(_("Importing archive..."))
        check_out(dbase, revision, db_path, None)
        self.__end_cursor()
        dbase.close()

    def __remove_db(self, obj):
        """
        Callback associated with the Remove button. Get the selected
        row and data, then call the verification dialog.
        """
        store, node = self.selection.get_selected()
        path = store.get_path(node)
        self.data_to_delete = store[path]

        if len(path) == 1:
            QuestionDialog(
                _("Remove the '%s' family tree?") % self.data_to_delete[0],
                _("Removing this family tree will permanently destroy the data."),
                _("Remove family tree"),
                self.__really_delete_db)
        else:
            rev = self.data_to_delete[0]
            parent = store[(path[0],)][0]
            QuestionDialog(
                _("Remove the '%(revision)s' version of '%(database)s'") % {
                    'revision' : rev, 
                    'database' : parent
                    },
                _("Removing this version will prevent you from "
                  "extracting it in the future."),
                _("Remove version"),
                self.__really_delete_version)

    def __really_delete_db(self):
        """
        Delete the selected database. If the database is open, close it first.
        Then scan the database directory, deleting the files, and finally
        removing the directory.
        """

        # close the database if the user has requested to delete the
        # active database
        if self.data_to_delete[PATH_COL] == self.active:
            self.dbstate.no_database()
            
        store, node = self.selection.get_selected()
        path = store.get_path(node)
        node = self.model.get_iter(path)
        filename = self.model.get_value(node, FILE_COL)
        try:
            name_file = open(filename, "r")
            file_name_to_delete=name_file.read()
            name_file.close()
            RecentFiles.remove_filename(file_name_to_delete)
            for (top, dirs, files) in os.walk(self.data_to_delete[1]):
                for filename in files:
                    os.unlink(os.path.join(top, filename))
            os.rmdir(self.data_to_delete[1])
        except (IOError, OSError), msg:
            DbManager.ERROR(_("Could not delete family tree"),
                                       str(msg))
        # rebuild the display
        self.__populate()
            
    def __really_delete_version(self):
        """
        Delete the selected database. If the database is open, close it first.
        Then scan the database directory, deleting the files, and finally
        removing the directory.
        """
        db_dir = self.data_to_delete[FILE_COL]
        rev = self.data_to_delete[PATH_COL]
        archive = os.path.join(db_dir, ARCHIVE_V)

        cmd = [ "rcs", "-x,v", "-o%s" % rev, "-q", archive ]

        proc = subprocess.Popen(cmd, stderr = subprocess.PIPE)
        status = proc.wait()
        message = "\n".join(proc.stderr.readlines())
        proc.stderr.close()
        del proc

        if status != 0:
            DbManager.ERROR(
                _("Deletion failed"),
                _("An attempt to delete a version failed "
                  "with the following message:\n\n%s") % message
                )

        # rebuild the display
        self.__populate()
            
    def __rename_db(self, obj):
        """
        Start the rename process by calling the start_editing option on 
        the line with the cursor.
        """
        store, node = self.selection.get_selected()
        path = self.model.get_path(node)
        self.name_renderer.set_property('editable', True)
        self.dblist.set_cursor(path, focus_column=self.column, 
                               start_editing=True)

    def __repair_db(self, obj):
        """
        Start the repair process by calling the start_editing option on 
        the line with the cursor.
        """
        store, node = self.selection.get_selected()
        dirname = store[node][1]
        
        #First ask user if he is really sure :-)
        yes_no = QuestionDialog2(
            _("Repair family tree?"),
            _(
"If you click <b>Proceed</b>, Gramps will attempt to recover your family tree"
" from the last good backup. There are several ways this can cause unwanted"
" effects, so <b>backup</b> the family tree first.\n"
"The Family tree you have selected is stored in %s.\n\n"
"Before doing a repair, verify that the Family Tree can really no longer be "
" opened, as the database back-end can recover from some errors automatically.\n\n"
"<b>Details:</b> Repairing a Family Tree actually uses the last backup of"
" the Family Tree, which Gramps stored on last use. If you have worked for"
" several hours/days without closing Gramps, then all this information will"
" be lost! If the repair fails, then the original family tree will be lost"
" forever, hence a backup is needed. If the repair fails, or too much"
" information is lost, you can fix the original family tree manually."
" For details, see the webpage\n"
"http://gramps-project.org/wiki/index.php?title=Recover_corrupted_family_tree\n"
"Before doing a repair, try to open the family tree in the normal manner."
" Several errors that trigger the repair button can be fixed automatically."
" If this is the case, you can disable the repair button by removing the"
" file <i>need_recover</i> in the family tree directory."
) % dirname,
            _("Proceed, I have taken a backup"),
            _("Stop"))
        prompt = yes_no.run()
        if not prompt:
            return
        
        opened = store[node][OPEN_COL]
        if opened:
            self.dbstate.no_database()
        
        # delete files that are not backup files or the .txt file
        for filename in os.listdir(dirname):
            if os.path.splitext(filename)[1] not in (".gbkp", ".txt"):
                fname = os.path.join(dirname, filename)
                os.unlink(fname)

        newdb = DbBsddb()
        newdb.write_version(dirname)

        dbclass = DbBsddb
        dbase = dbclass()
        dbase.set_save_path(dirname)
        dbase.load(dirname, None)

        self.__start_cursor(_("Rebuilding database from backup files"))
        
        try:
            restore(dbase)
        except DbException, msg:
            DbManager.ERROR(_("Error restoring backup data"), msg)

        self.__end_cursor()

        dbase.close()
        self.dbstate.no_database()
        self.__populate()

    def __start_cursor(self, msg):
        """
        Set the cursor to the busy state, and displays the associated
        message
        """
        self.msg.set_label(msg)
        self.top.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        while (gtk.events_pending()):
            gtk.main_iteration()

    def __end_cursor(self):
        """
        Set the cursor back to normal and clears the message
        """
        self.top.window.set_cursor(None)
        self.msg.set_label("")

    def __new_db(self, obj):
        """
        Callback wrapper around the actual routine that creates the
        new database. Catch OSError and IOError and display a warning 
        message.
        """
        self.new.set_sensitive(False)
        try:
            self._create_new_db()
        except (OSError, IOError), msg:
            DbManager.ERROR(_("Could not create family tree"),
                                       str(msg))
        self.new.set_sensitive(True)

    def _create_new_db(self, title=None):
        """
        Create a new database, append to model
        """
        new_path, title = self.create_new_db_cli(title)
        path_name = os.path.join(new_path, NAME_FILE)
        (tval, last) = time_val(new_path)
        node = self.model.append(None, [title, new_path, path_name, 
                                        last, tval, False, ''])
        self.selection.select_iter(node)
        path = self.model.get_path(node)
        self.name_renderer.set_property('editable', True)
        self.dblist.set_cursor(path, focus_column=self.column, 
                               start_editing=True)
        return new_path, title

    def __drag_data_received(self, widget, context, xpos, ypos, selection, 
                             info, rtime):
        """
        Handle the reception of drag data
        """
        drag_value = selection.data
        fname = None
        type = None
        title = None
        # Allow any type of URL ("file://", "http://", etc):
        if drag_value and urlparse.urlparse(drag_value).scheme != "":
            fname, title = [], []
            for treename in [v.strip() for v in drag_value.split("\n") if v.strip() != '']:
                f, t = self.import_new_db(treename, None)
                fname.append(f)
                title.append(t)
        return fname, title

def drag_motion(wid, context, xpos, ypos, time_stamp):
    """
    DND callback that is called on a DND drag motion begin
    """
    context.drag_status(gtk.gdk.ACTION_COPY, time_stamp)
    return True

def drop_cb(wid, context, xpos, ypos, time_stamp):
    """
    DND callback that finishes the DND operation
    """
    context.finish(True, False, time_stamp)
    return True

def find_revisions(name):
    """
    Finds all the revisions of the specified RCS archive.
    """
    import re

    rev  = re.compile("\s*revision\s+([\d\.]+)")
    date = re.compile("date:\s+(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)[-+]\d\d;")

    if not os.path.isfile(name) or not _RCS_FOUND:
        return []

    rlog = [ "rlog", "-x,v", "-zLT" , name ]

    proc = subprocess.Popen(rlog, stdout = subprocess.PIPE)
    proc.wait()

    revlist = []
    date_str = ""
    rev_str = ""
    com_str = ""
    
    get_next = False
    if os.path.isfile(name):
        for line in proc.stdout:
            match = rev.match(line)
            if match:
                rev_str = copy.copy(match.groups()[0])
                continue
            match = date.match(line)
            if match:
                date_str = time.strftime('%x %X',
                        time.strptime(match.groups()[0], '%Y-%m-%d %H:%M:%S'))
                
                get_next = True
                continue
            if get_next:
                get_next = False
                com_str = line.strip()
                revlist.append((rev_str, date_str, com_str))
    proc.stdout.close()
    del proc
    return revlist



def check_out(dbase, rev, path, callback):
    """
    Checks out the revision from rcs, and loads the resulting XML file
    into the database.
    """
    co_cmd   = [ "co", "-x,v", "-q%s" % rev] + [ os.path.join(path, ARCHIVE),
                                                 os.path.join(path, ARCHIVE_V)]

    proc = subprocess.Popen(co_cmd, stderr = subprocess.PIPE)
    status = proc.wait()
    message = "\n".join(proc.stderr.readlines())
    proc.stderr.close()
    del proc

    if status != 0:
        ErrorDialog(
            _("Retrieve failed"),
            _("An attempt to retrieve the data failed "
              "with the following message:\n\n%s") % message
            )
        return 

    pmgr = GuiPluginManager.get_instance()
    for plugin in pmgr.get_import_plugins():
        if plugin.get_extension() == "gramps":
            rdr = plugin.get_import_function()

    xml_file = os.path.join(path, ARCHIVE)
    rdr(dbase, xml_file, callback)
    os.unlink(xml_file)

def check_in(dbase, filename, callback, cursor_func = None):
    """
    Checks in the specified file into RCS
    """
    init   = [ "rcs", '-x,v', '-i', '-U', '-q', '-t-"Gramps database"' ]
    ci_cmd = [ "ci", '-x,v', "-q", "-f" ]
    archive_name = filename + ",v"
    
    glade = Glade(toplevel='comment')
    top = glade.toplevel
    text = glade.get_object('description')
    top.run()
    comment = text.get_text()
    top.destroy()

    if not os.path.isfile(archive_name):
        cmd = init + [archive_name]
        proc = subprocess.Popen(cmd,
                                stderr = subprocess.PIPE)
        status = proc.wait()
        message = "\n".join(proc.stderr.readlines())
        proc.stderr.close()
        del proc
        
        if status != 0:
            ErrorDialog(
                _("Archiving failed"),
                _("An attempt to create the archive failed "
                  "with the following message:\n\n%s") % message
                )

    if cursor_func:
        cursor_func(_("Creating data to be archived..."))
        
    plugin_manager = GuiPluginManager.get_instance()
    for plugin in plugin_manager.get_export_plugins():
        if plugin.get_extension() == "gramps":
            export_function = plugin.get_export_function()
            export_function(dbase, filename, None, callback)

    if cursor_func:
        cursor_func(_("Saving archive..."))
        
    cmd = ci_cmd + ['-m%s' % comment, filename, archive_name ]
    proc = subprocess.Popen(cmd, 
                            stderr = subprocess.PIPE)

    status = proc.wait()
    message = "\n".join(proc.stderr.readlines())
    proc.stderr.close()
    del proc

    if status != 0:
        ErrorDialog(
            _("Archiving failed"),
            _("An attempt to archive the data failed "
              "with the following message:\n\n%s") % message
            )
