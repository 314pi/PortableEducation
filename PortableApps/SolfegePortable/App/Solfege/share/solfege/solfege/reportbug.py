# GNU Solfege - free ear training software
# Copyright (C) 2005, 2007, 2008, 2011 Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import random
import string
import sys
import urllib
import urllib2

import gtk

from solfege import buildinfo
from solfege import cfg
from solfege import gu
from solfege import utils

RESPONSE_SEND = 1011

class ReportBugWindow(gtk.Dialog):
    def __init__(self, parent, error_text):
        gtk.Dialog.__init__(self, _("Make bug report"), parent,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.m_error_text = error_text
        self.add_button(_("_Send"), RESPONSE_SEND)
        self.set_default_size(400, 400)
        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        l = gtk.Label(_("Information about the version of GNU Solfege, your operating system and Python version, and the Python traceback (error message) will be sent to the crash database. Your email will not be published or shared, but we might contact you by email if we have further questions about your crash report."))
        l.set_line_wrap(True)
        l.show()
        self.vbox.pack_start(l, False)
        self.g_email = gtk.Entry()
        self.vbox.pack_start(
            gu.hig_label_widget(_("_Email:"), self.g_email, sizegroup),
            False)
        self.g_email.set_text(cfg.get_string('user/email'))
        # 140 is max in the solfege.org database
        self.g_description = gtk.Entry(max=140)
        self.vbox.pack_start(
            gu.hig_label_widget(_("S_hort description:"), self.g_description,
                     sizegroup), False)
        label = gtk.Label(_("_Describe how to produce the error message:"))
        label.set_use_underline(True)
        label.set_alignment(0.0, 0.5)
        self.vbox.pack_start(label, False)
        self.g_tw = gtk.TextView()
        self.g_tw.set_wrap_mode(gtk.WRAP_WORD)
        self.g_tw.set_border_width(10)
        label.set_mnemonic_widget(self.g_tw)
        self.vbox.pack_start(self.g_tw)
        self.show_all()
    def send_bugreport(self):
        """
        Return None if successful. Return the urllib2 execption if failure.
        """
        try:
            windowsversion = str(sys.getwindowsversion())
        except AttributeError:
            windowsversion = "(not running ms windows)"
        buf = self.g_tw.get_buffer()
        description = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        data = urllib.urlencode({
            'email': self.g_email.get_text(),
            'version': buildinfo.VERSION_STRING,
            'revision_id': buildinfo.REVISION_ID,
            'pygtk_version': str(gtk.pygtk_version),
            'gtk': str(gtk),
            'sys.version': sys.version,
            'sys.platform': sys.platform,
            'windowsversion': windowsversion, 
            'short_description': self.g_description.get_text(),
            'description': description,
            'traceback': self.m_error_text,
        })
        urllib2.urlopen("http://www.solfege.org/crashreport/", data)
        return

