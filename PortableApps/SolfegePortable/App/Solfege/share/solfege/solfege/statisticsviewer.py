# vim:set fileencoding=utf-8:
# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2006, 2007, 2008, 2011  Tom Cato Amundsen
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
from __future__ import division

import datetime

import gtk

import solfege
from solfege import gu
from solfege import lessonfile
from solfege import lessonfilegui

display_max_num_tests = 10

def label_from_key(statistics, key):
    try:
        v = eval(key)
    except Exception:
        v = key
    else:
        if isinstance(v, (int, float, long)):
            v = key
    if not v:
        l = gtk.Label(key)
    elif hasattr(statistics, 'm_key_is_list'):
        l = lessonfilegui.LabelObjectBox(statistics.m_t.m_P, v)
    else:
        l = lessonfilegui.new_labelobject(statistics.key_to_pretty_name(v))
    l.set_alignment(0.0, 0.5)
    return l


class SimpleTable(gtk.VBox):
    def __init__(self, heading, statistics):
        gtk.VBox.__init__(self)
        self.m_heading = heading
        self.m_data = []
        self.m_statistics = statistics
    def add_row(self, cell1, cell2):
        self.m_data.append((cell1, cell2))
    def create(self):
        table = gtk.Table()
        label = gtk.Label()
        label.set_alignment(0.0, 0.5)
        label.set_markup(u"<b>%s</b>" % self.m_heading)
        self.pack_start(label)
        for idx, (cell1, cell2) in enumerate(self.m_data):
            table.attach(label_from_key(self.m_statistics, cell1), 1, 2, idx*2+1, idx*2+2,
                         xoptions=gtk.SHRINK, xpadding=2)
            table.attach(gtk.Label(cell2), 3, 4, idx*2+1, idx*2+2,
                         xoptions=gtk.SHRINK, xpadding=2)
        for idx in range(len(self.m_data) + 1):
            table.attach(gtk.HSeparator(), 0, 5, idx*2, idx*2+1, xoptions=gtk.FILL)
        table.attach(gtk.VSeparator(), 0, 1, 0, idx*2+2, xoptions=gtk.SHRINK)
        table.attach(gtk.VSeparator(), 2, 3, 0, idx*2+2, xoptions=gtk.SHRINK)
        table.attach(gtk.VSeparator(), 4, 5, 0, idx*2+2, xoptions=gtk.SHRINK)
        self.pack_start(table, False)
        self.show_all()

class MatrixTable(gtk.VBox):
    def __init__(self, heading, st_data, st):
        """
        st_data is the statistics data we want displayled
        st is the statistics object the statistics are collected from.
        """
        gtk.VBox.__init__(self)
        label = gtk.Label(heading)
        label.set_name("StatisticsH2")
        label.set_alignment(0.0, 0.0)
        self.pack_start(label, False)
        hbox = gu.bHBox(self, False)
        frame = gtk.Frame()
        hbox.pack_start(frame, False)
        t = gtk.Table()
        frame.add(t)
        keys = st.get_keys(True)
        for x in range(len(keys)):
            t.attach(gtk.VSeparator(), x*2+1, x*2+2, 0, len(keys)*2)
        for x in range(len(keys)-1):
            t.attach(gtk.HSeparator(), 0, len(keys)*2+1, x*2+1, x*2+2)
        for y, key in enumerate(keys):
            l = label_from_key(st, key)
            t.attach(l, 0, 1, y*2, y*2+1, xpadding=gu.PAD)
            for x, skey in enumerate(keys):
                try:
                    s = st_data[key][skey]
                except KeyError:
                    s = '-'
                l = gtk.Label(s)
                if x == y:
                    l.set_name('BoldText')
                t.attach(l, x*2+2, x*2+3, y*2, y*2+1, xpadding=gu.PAD)
        self.show_all()


class PercentagesTable(gtk.Frame):
    def __init__(self, statistics):
        gtk.Frame.__init__(self)
        table = gtk.Table()
        self.add(table)
        self.boxdict = {}
        self.m_totals = {}
        #       0     1  2    3 4     5 6       7     8
        # 0  -------------------------------------------
        # 1  |        |   Session     |     Today     |
        # 2  |        | Percent Count | Percent Count |
        # 3  +------ ----------------------------------
        # 4  | Total  |  85%  | 13    |
        # 5  +-------------------------
        # 6  | label1 |  100% | 4     |
        #    | label2 |   50% | 5     |
        # 7  +-----------------------------------------
        for k, l, x in (('session', _("Session"), 2), ('today', _("Today"), 5),
                     ('last7', _("Last 7 days"), 8), ('total', _("Total"), 11)):
            table.attach(gtk.Label(l), x, x+2, 0, 1,
                         xpadding=gu.PAD_SMALL, ypadding=gu.PAD_SMALL)
            b = gtk.VBox()
            table.attach(b, x, x+1, 6, 7)
            self.boxdict[k+'percent'] = b
            b = gtk.VBox()
            table.attach(b, x+1, x+2, 6, 7)
            self.boxdict[k+'count'] = b
            l = gtk.Label()
            table.attach(l, x, x+1, 4, 5)
            self.m_totals[k+'percent'] = l
            l = gtk.Label()
            table.attach(l, x+1, x+2, 4, 5)
            self.m_totals[k+'count'] = l
        for x in (2, 5, 8, 11):
            table.attach(gtk.Label(_("Percent")), x, x+1, 1, 2,
                         xpadding=gu.PAD_SMALL, ypadding=gu.PAD_SMALL)
            table.attach(gtk.Label(_("Count")), x+1, x+2, 1, 2,
                         xpadding=gu.PAD_SMALL, ypadding=gu.PAD_SMALL)
        l = gtk.Label(_("Total"))
        l.set_alignment(0.0, 0.5)
        table.attach(l, 0, 1, 4, 5, xpadding=gu.PAD_SMALL, ypadding=gu.PAD_SMALL)
        table.attach(gtk.HSeparator(), 0, 13, 3, 4)
        table.attach(gtk.HSeparator(), 0, 13, 5, 6)
        table.attach(gtk.VSeparator(), 1, 2, 0, 7)
        table.attach(gtk.VSeparator(), 4, 5, 0, 7)
        table.attach(gtk.VSeparator(), 7, 8, 0, 7)
        table.attach(gtk.VSeparator(), 10, 11, 0, 7)
        self.boxdict['keys'] = key_box = gtk.VBox()
        table.attach(key_box, 0, 1, 6, 7)
        for key, box in self.boxdict.items():
            box.set_border_width(gu.PAD_SMALL)
        self.update(statistics)
        self.show_all()
    def update(self, statistics):
        for box in self.boxdict.values():
            for o in box.get_children():
                o.destroy()
        for sk, seconds in (('session', 0),
                       ('today', 60*60*24),
                       ('last7', 60*60*24*7),
                       ('total', -1)):
            num_guess = statistics.get_num_guess(seconds)
            if num_guess == 0:
                self.m_totals[sk+'percent'].set_text("-")
            else:
                self.m_totals[sk+'percent'].set_text(u"%.0f%%" % 
                   (statistics.get_num_correct(seconds) / num_guess * 100))
            self.m_totals[sk+'count'].set_text(unicode(num_guess))
        for k in statistics.get_keys(True):
            l = label_from_key(statistics, k)
            self.boxdict['keys'].pack_start(l)
            for sk, seconds in (('session', 0),
                       ('today', 60*60*24),
                       ('last7', 60*60*24*7),
                       ('total', -1)):
                num_guess = statistics.get_num_guess_for_key(seconds, k)
                if num_guess == 0:
                    self.boxdict[sk+'percent'].pack_start(gtk.Label("-"))
                else:
                    self.boxdict[sk+'percent'].pack_start(
                        gtk.Label("%.0f%%" % (statistics.get_num_correct_for_key(seconds, k) / num_guess * 100)))
                self.boxdict[sk+'count'].pack_start(gtk.Label(unicode(num_guess)))
        self.show_all()


class StatisticsViewer(gtk.ScrolledWindow):
    def __init__(self, statistics, heading):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(gu.PAD)
        self.vbox.set_border_width(gu.PAD)
        self.add_with_viewport(self.vbox)
        hbox = gtk.HBox()
        hbox.set_spacing(gu.hig.SPACE_SMALL)
        im = gtk.image_new_from_file("graphics/applications-system.svg")
        self.g_settings_button = b = gtk.Button()
        b.connect('clicked', self.on_delete_statistics)
        b.add(im)
        hbox.pack_start(b, False)
        self.g_heading = gtk.Label(heading)
        self.g_heading.set_alignment(0.0, 0.5)
        self.g_heading.set_name("StatisticsH1")
        hbox.pack_start(self.g_heading, False)
        self.vbox.pack_start(hbox, False)
        self.m_statistics = statistics
        self.g_tables = gtk.VBox()
        self.g_tables.show()
        self.vbox.pack_start(self.g_tables)
        self.show_all()
    def update(self):
        self.clear()
        self.g_settings_button.set_sensitive(solfege.db.get_session_count(
                solfege.db.get_fileid(self.m_statistics.m_t.m_P.m_filename)))

        self.g_p = PercentagesTable(self.m_statistics)
        self.g_p.show_all()
        self.g_tables.pack_start(self.g_p, False)
        if self.m_statistics.m_t.m_P.header.statistics_matrices in (
            'enabled', 'hidden'):
            self.g_tables.pack_start(self.create_matrices_expander(), False)
        c = 0
        for time, f, result in self.m_statistics.iter_test_results():
            t = datetime.datetime.fromtimestamp(time)
            if self.m_statistics.m_t.m_P.header.statistics_matrices == 'enabled':
                m = MatrixTable(_(u"Test dated %(date)s: %(percent).1f%%") % {
                    'date': t.strftime("%x %X"),
                    'percent': f}, result, self.m_statistics)
                m.show()
                self.g_tables.pack_start(m, False)
            else:
                num_x_per_question = lessonfile.parse_test_def(self.m_statistics.m_t.m_P.header.test)[0]
                b = SimpleTable(_(u"Test dated %(date)s: %(percent).1f%%") % {
                    'date': t.strftime("%x %X"),
                    'percent': f
                }, self.m_statistics)
                for k in result:
                    count = result[k].get(k, 0)
                    # More necessary than one would expect because we want to handle
                    # the possibility that that result[key1][key2] == None
                    # A user has reported that this can happen, but I don't know
                    # what could insert a None into the database.
                    if count is None:
                        count = 0
                    b.add_row(k, "%.1f%%" % (100 * count / num_x_per_question))
                b.create()
                self.g_tables.pack_start(b, False)
            # Don't show too many test results.
            c += 1
            if c == display_max_num_tests:
                break
    def create_matrices_expander(self):
        expander = gtk.Expander()
        expander.connect_after('activate', self.on_expander_activate)
        vbox = gtk.VBox()
        expander.add(vbox)
        if self.m_statistics.m_t.m_P.header.statistics_matrices == 'enabled':
            expander.set_expanded(True)
            for heading, seconds in ((_("Session"), 0),
                                     (_("Today"), 60*60*24),
                                     (_("Last 7 days"), 60*60*24*7),
                                     (_("Total"), -1)):
                table = MatrixTable(heading,
                                    self.m_statistics.get_statistics(seconds),
                                    self.m_statistics)
                vbox.pack_start(table, False)
        else:
            expander.set_expanded(False)
        expander.show_all()
        return expander
    def on_expander_activate(self, expander):
        self.m_statistics.m_t.m_P.header['statistics_matrices'] = {
            True: 'enabled',
            False: 'hidden'}[expander.get_expanded()]
        self.update()
    def clear(self):
        #UGH why cant we just destroy the children of g_tables??!!
        #for c in self.g_tables.children():
        #    c.destroy()
        self.g_tables.destroy()
        self.g_tables = gtk.VBox()
        self.g_tables.set_spacing(gu.hig.SPACE_LARGE)
        self.g_tables.show()
        self.vbox.pack_start(self.g_tables)
    def on_delete_statistics(self, widget):
        class Dlg(gtk.MessageDialog):
            def __init__(self, first, last, count):
                gtk.MessageDialog.__init__(self, None, gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_QUESTION,
                                    gtk.BUTTONS_YES_NO,
                                    _("Delete statistics and test results?"))
                self.format_secondary_text(_("This exercise have statistics from %(count)s practise sessions, from %(first)s to %(last)s") % {
                    'count': count,
                    'first': first.strftime("%x %X"),
                    'last': last.strftime("%x %X")})
                self.show_all()
        fileid = solfege.db.get_fileid(self.m_statistics.m_t.m_P.m_filename)
        first = datetime.datetime.fromtimestamp(solfege.db.get_first_timestamp(fileid))
        last = datetime.datetime.fromtimestamp(solfege.db.get_last_timestamp(fileid))
        count = solfege.db.get_session_count(fileid)
        dlg = Dlg(first, last, count)
        ret = dlg.run()
        if ret == gtk.RESPONSE_YES:
            solfege.db.delete_statistics(self.m_statistics.m_t.m_P.m_filename)
            self.update()
        dlg.destroy()

