#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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
# Standard python modules
#
#-------------------------------------------------------------------------
import sys

#-------------------------------------------------------------------------
#
# GNOME/GTK+ modules
#
#-------------------------------------------------------------------------
import gtk
from gtk.gdk import pixbuf_new_from_file

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
import const
import config
from glade import Glade
from gen.ggettext import gettext as _

try:
    ICON = pixbuf_new_from_file(const.ICON)
except:
    ICON = None

class SaveDialog(object):
    def __init__(self, msg1, msg2, task1, task2, parent=None):
        self.xml = Glade(toplevel='savedialog')
        
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % msg1)
        
        self.dontask = self.xml.get_object('dontask')
        self.task1 = task1
        self.task2 = task2
        
        label1 = self.xml.get_object('sd_label1')
        label1.set_text('<span weight="bold" size="larger">%s</span>' % msg1)
        label1.set_use_markup(True)
        
        label2 = self.xml.get_object('sd_label2')
        label2.set_text(msg2)
        label2.set_use_markup(True)
        if parent:
            self.top.set_transient_for(parent)
        self.top.show()
        response = self.top.run()
        if response == gtk.RESPONSE_NO:
            self.task1()
        elif response == gtk.RESPONSE_YES:
            self.task2()

        config.set('interface.dont-ask', self.dontask.get_active())
        self.top.destroy()

class QuestionDialog(object):
    def __init__(self, msg1, msg2, label, task, parent=None):
        self.xml = Glade(toplevel='questiondialog')
                
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % msg1)

        label1 = self.xml.get_object('qd_label1')
        label1.set_text('<span weight="bold" size="larger">%s</span>' % msg1)
        label1.set_use_markup(True)
        
        label2 = self.xml.get_object('qd_label2')
        label2.set_text(msg2)
        label2.set_use_markup(True)

        self.xml.get_object('okbutton').set_label(label)

        if parent:
            self.top.set_transient_for(parent)
        self.top.show()
        response = self.top.run()
        self.top.destroy()
        if response == gtk.RESPONSE_ACCEPT:
            task()

from GrampsDisplay import url as display_url
def on_activate_link(label, uri):
    # see aboutdialog.py _show_url()
    display_url(uri)
    return True

class QuestionDialog2(object):
    def __init__(self, msg1, msg2, label_msg1, label_msg2, parent=None):
        self.xml = Glade(toplevel='questiondialog')
              
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % msg1)

        label1 = self.xml.get_object('qd_label1')
        label1.set_text('<span weight="bold" size="larger">%s</span>' % msg1)
        label1.set_use_markup(True)
        
        label2 = self.xml.get_object('qd_label2')
        # see https://github.com/emesene/emesene/issues/723
        label2.connect('activate-link', on_activate_link)
        label2.set_text(msg2)
        label2.set_use_markup(True)

        self.xml.get_object('okbutton').set_label(label_msg1)
        self.xml.get_object('okbutton').set_use_underline(True)
        self.xml.get_object('no').set_label(label_msg2)
        self.xml.get_object('no').set_use_underline(True)
        
        if parent:
            self.top.set_transient_for(parent)
        self.top.show()

    def run(self):
        response = self.top.run()
        self.top.destroy()
        return (response == gtk.RESPONSE_ACCEPT)

class OptionDialog(object):
    def __init__(self, msg1, msg2, btnmsg1, task1, btnmsg2, task2, parent=None):
        self.xml = Glade(toplevel='optiondialog')
              
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % msg1)

        label1 = self.xml.get_object('od_label1')
        label1.set_text('<span weight="bold" size="larger">%s</span>' % msg1)
        label1.set_use_markup(True)
        
        label2 = self.xml.get_object('od_label2')
        label2.set_text(msg2)
        label2.set_use_markup(True)

        self.xml.get_object('option1').set_label(btnmsg1)
        self.xml.get_object('option2').set_label(btnmsg2)
        if parent:
            self.top.set_transient_for(parent)
        self.top.show()
        self.response = self.top.run()
        if self.response == gtk.RESPONSE_NO:
            if task1:
                task1()
        else:
            if task2:
                task2()
        self.top.destroy()

    def get_response(self):
        return self.response

class ErrorDialog(gtk.MessageDialog):
    def __init__(self, msg1, msg2="", parent=None):
        
        gtk.MessageDialog.__init__(self, parent,
                                   flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_CLOSE)
        self.set_markup('<span weight="bold" size="larger">%s</span>' % msg1)
        self.format_secondary_text(msg2)
        self.set_icon(ICON)
        self.set_title("%s - Gramps" % msg1)
        self.show()
        self.run()
        self.destroy()

class RunDatabaseRepair(ErrorDialog):
    def __init__(self, msg, parent=None):
        msg = unicode(str(msg).decode(sys.getfilesystemencoding()))
        ErrorDialog.__init__(
            self,
            _('Error detected in database'),
            _('Gramps has detected an error in the database. This can '
              'usually be resolved by running the "Check and Repair Database" '
              'tool.\n\nIf this problem continues to exist after running this '
              'tool, please file a bug report at '
              'http://bugs.gramps-project.org\n\n') + msg, parent)

class DBErrorDialog(ErrorDialog):
    def __init__(self, msg, parent=None):
        msg = unicode(str(msg).decode(sys.getfilesystemencoding()))
        ErrorDialog.__init__(
            self,
            _("Low level database corruption detected"),
            _("Gramps has detected a problem in the underlying "
              "Berkeley database. This can be repaired from "
              "the Family Tree Manager. Select the database and "
              'click on the Repair button') + '\n\n' + msg, parent)

class WarningDialog(gtk.MessageDialog):
    def __init__(self, msg1, msg2="", parent=None):

        gtk.MessageDialog.__init__(self, parent,
                                   flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_WARNING,
                                   buttons=gtk.BUTTONS_CLOSE)
        self.set_markup('<span weight="bold" size="larger">%s</span>' % msg1)
        self.format_secondary_markup(msg2)
        # FIXME: Hyper-links in the secondary text display as underlined text,
        # but clicking on the link fails with
        # GtkWarning: Unable to show 'http://www.gramps-project.org/wiki/index.php?title=How_to_make_a_backup': Operation not supported
        # self.connect('activate-link'... fails with
        # <WarningDialog object at 0x4880300 (GtkMessageDialog at 0x5686010)>: unknown signal name: activate-link
        self.set_icon(ICON)
        self.set_title("%s - Gramps" % msg1)
        self.show()
        self.run()
        self.destroy()

class OkDialog(gtk.MessageDialog):
    def __init__(self, msg1, msg2="", parent=None):

        gtk.MessageDialog.__init__(self, parent,
                                   flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_CLOSE)
        self.set_markup('<span weight="bold" size="larger">%s</span>' % msg1)
        self.format_secondary_text(msg2)
        self.set_icon(ICON)
        self.set_title("%s - Gramps" % msg1)
        self.show()
        self.run()
        self.destroy()

class InfoDialog(object):
    """
    Non modal dialog to show selectable info in a scrolled window
    """
    def __init__(self, msg1, infotext, parent=None, monospaced=False):
        self.xml = Glade(toplevel='infodialog')
              
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % msg1)

        label = self.xml.get_object('toplabel')
        label.set_text('<span weight="bold" size="larger">%s</span>' % msg1)
        label.set_use_markup(True)
        
        infoview = self.xml.get_object('infoview')
        infobuffer = gtk.TextBuffer()
        infobuffer.set_text(infotext)
        if monospaced:
            startiter, enditer = infobuffer.get_bounds()
            tag = infobuffer.create_tag(family="Monospace")
            infobuffer.apply_tag(tag, startiter, enditer)
        infoview.set_buffer(infobuffer)

        if parent:
            self.top.set_transient_for(parent)
        self.top.connect('response', self.destroy)
        self.top.show()

    def destroy(self, dialog, response_id):
        #no matter how it finishes, destroy dialog
        dialog.destroy()

class MissingMediaDialog(object):
    def __init__(self, msg1, msg2, task1, task2, task3, parent=None):
        self.xml = Glade(toplevel='missmediadialog')
              
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % msg1)

        self.task1 = task1
        self.task2 = task2
        self.task3 = task3
        
        label1 = self.xml.get_object('label4')
        label1.set_text('<span weight="bold" size="larger">%s</span>' % msg1)
        label1.set_use_markup(True)
        
        label2 = self.xml.get_object('label3')
        label2.set_text(msg2)
        label2.set_use_markup(True)

        check_button = self.xml.get_object('use_always')

        if parent:
            self.top.set_transient_for(parent)
        self.top.show()
        self.top.connect('delete_event', self.warn)
        response = gtk.RESPONSE_DELETE_EVENT

        # Need some magic here, because an attempt to close the dialog
        # with the X button not only emits the 'delete_event' signal
        # but also exits with the RESPONSE_DELETE_EVENT
        while response == gtk.RESPONSE_DELETE_EVENT:
            response = self.top.run()

        if response == 1:
            self.task1()
        elif response == 2:
            self.task2()
        elif response == 3:
            self.task3()
        if check_button.get_active():
            self.default_action = response
        else:
            self.default_action = 0
        self.top.destroy()

    def warn(self, obj, obj2):
        WarningDialog(
            _("Attempt to force closing the dialog"),
            _("Please do not force closing this important dialog.\n"
              "Instead select one of the available options"),
            self.top)
        return True

class MessageHideDialog(object):
    
    def __init__(self, title, message, key, parent=None):
        self.xml = Glade(toplevel='hidedialog')
              
        self.top = self.xml.toplevel
        self.top.set_icon(ICON)
        self.top.set_title("%s - Gramps" % title)

        dont_show = self.xml.get_object('dont_show')
        dont_show.set_active(config.get(key))
        title_label = self.xml.get_object('title')
        title_label.set_text(
            '<span size="larger" weight="bold">%s</span>' % title)
        title_label.set_use_markup(True)
        
        self.xml.get_object('message').set_text(message)
        
        dont_show.connect('toggled', self.update_checkbox, key)
        self.top.run()
        self.top.destroy()

    def update_checkbox(self, obj, constant):
        config.set(constant, obj.get_active())
        config.save()
