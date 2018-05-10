#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2008  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2008       Gary Burton
# Copyright (C) 2008       Robert Cheramy <robert@cheramy.net>
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

# $Id$

"Export to GRAMPS package"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import time
import shutil
import os
import sys
import tarfile
from cStringIO import StringIO
from gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".WritePkg")

#-------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from ExportOptions import WriterOptionBox
import gen.proxy
from ExportXml import XmlWriter
import Utils
import constfunc

#-------------------------------------------------------------------------
#
# writeData
#
#-------------------------------------------------------------------------
def writeData(database, filename, msg_callback, option_box=None, callback=None):

# Rename file, if it exists already, with <filename>.bak
# as it it for normal XML export.

    if os.path.isfile(filename):
        try:
            shutil.copyfile(filename, filename + ".bak")
            shutil.copystat(filename, filename + ".bak")
        except:
            pass

    if option_box:
        option_box.parse_options()
        database = option_box.get_filtered_database(database)

    writer = PackageWriter(database, filename, msg_callback, callback)
    return writer.export()
    
#-------------------------------------------------------------------------
#
# PackageWriter
#
#-------------------------------------------------------------------------
class PackageWriter(object):

    def __init__(self, database, filename, msg_callback, callback=None):
        self.db = database
        self.callback = callback
        self.msg_callback = msg_callback
        self.filename = filename
            
    def export(self):
#        missmedia_action = 0
        #--------------------------------------------------------------
        def remove_clicked():
            # File is lost => remove all references and the object itself
            for p_id in self.db.iter_family_handles():
                p = self.db.get_family_from_handle(p_id)
                nl = p.get_media_list()
                for o in nl:
                    if o.get_reference_handle() == m_id:
                        nl.remove(o) 
                p.set_media_list(nl)
                self.db.commit_family(p,None)
            for key in self.db.iter_person_handles():
                p = self.db.get_person_from_handle(key)
                nl = p.get_media_list()
                for o in nl:
                    if o.get_reference_handle() == m_id:
                        nl.remove(o) 
                p.set_media_list(nl)
                self.db.commit_person(p,None)
            for key in self.db.get_source_handles():
                p = self.db.get_source_from_handle(key)
                nl = p.get_media_list()
                for o in nl:
                    if o.get_reference_handle() == m_id:
                        nl.remove(o) 
                p.set_media_list(nl)
                self.db.commit_source(p,None)
            for key in self.db.get_place_handles():
                p = self.db.get_place_from_handle(key)
                nl = p.get_media_list()
                for o in nl:
                    if o.get_reference_handle() == m_id:
                        nl.remove(o) 
                p.set_media_list(nl)
                self.db.commit_place(p,None)
            for key in self.db.get_event_handles():
                p = self.db.get_event_from_handle(key)
                nl = p.get_media_list()
                for o in nl:
                    if o.get_reference_handle() == m_id:
                        nl.remove(o) 
                p.set_media_list(nl)
                self.db.commit_event(p,None)
            self.db.remove_object(m_id,None)

        def leave_clicked():
            # File is lost => do nothing, leave as is
            pass

        def select_clicked():
            # File is lost => select a file to replace the lost one
            def fs_close_window(obj):
                pass

            def fs_ok_clicked(obj):
                name = Utils.get_unicode_path_from_file_chooser(fs_top.get_filename())
                if os.path.isfile(name):
                    archive.add(name)
                    
            fs_top = gtk.FileChooserDialog("%s - GRAMPS" % _("Select file"),
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OK, gtk.RESPONSE_OK)
                        )
            response = fs_top.run()
            if response == gtk.RESPONSE_OK:
                fs_ok_clicked(fs_top)
            elif response == gtk.RESPONSE_CANCEL:
                fs_close_window(fs_top)

            fs_top.destroy()
        #---------------------------------------------------------------

        try:
            archive = tarfile.open(self.filename,'w:gz')
        except EnvironmentError, msg:
            log.warn(str(msg))
            self.msg_callback(_('Failure writing %s') % self.filename, str(msg))
            return 0
        
        # Write media files first, since the database may be modified 
        # during the process (i.e. when removing object)
        for m_id in self.db.get_media_object_handles(sort_handles=True):
            mobject = self.db.get_object_from_handle(m_id)
            filename = Utils.media_path_full(self.db, mobject.get_path())
            archname = str(mobject.get_path())
            if os.path.isfile(filename) and os.access(filename, os.R_OK):
                archive.add(filename, archname)
#             else:
#                 # File is lost => ask what to do
#                 if missmedia_action == 0:
#                     mmd = MissingMediaDialog(
#                         _("Media object could not be found"),
#                         _("%(file_name)s is referenced in the database, "
#                           "but no longer exists. The file may have been "
#                           "deleted or moved to a different location. " 
#                           "You may choose to either remove the reference "
#                           "from the database, keep the reference to the "
#                           "missing file, or select a new file."
#                           ) % { 'file_name' : filename },
#                         remove_clicked, leave_clicked, select_clicked)
#                     missmedia_action = mmd.default_action
#                 elif missmedia_action == 1:
#                     remove_clicked()
#                 elif missmedia_action == 2:
#                     leave_clicked()
#                 elif missmedia_action == 3:
#                     select_clicked()
        
        # Write XML now
        g = StringIO()
        gfile = XmlWriter(self.db, self.msg_callback, self.callback, 2)
        gfile.write_handle(g)
        tarinfo = tarfile.TarInfo('data.gramps')
        tarinfo.size = len(g.getvalue())
        tarinfo.mtime = time.time()
        if not constfunc.win():
            tarinfo.uid = os.getuid()
            tarinfo.gid = os.getgid()
        g.seek(0)
        archive.addfile(tarinfo, g)
        archive.close()
        g.close()

        return True
