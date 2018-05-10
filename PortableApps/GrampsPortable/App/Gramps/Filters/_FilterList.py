#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2007  Donald N. Allingham
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
# Standard Python modules
#
#-------------------------------------------------------------------------
from xml.sax import make_parser, SAXParseException
import os
import sys

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Filters._FilterParser import FilterParser
from gen.plug import BasePluginManager

PLUGMAN = BasePluginManager.get_instance()
#-------------------------------------------------------------------------
#
# FilterList
#
#-------------------------------------------------------------------------
class FilterList(object):
    """
    Container class for managing the generic filters.
    It stores, saves, and loads the filters.
    """
    
    def __init__(self, file):
        self.filter_namespaces = {}
        self.file = os.path.expanduser(file)
        self._cached = {}

    def get_filters_dict(self, namespace='generic'):
        """
        This runs every for every item to be matched! 
        """
        if self._cached.get(namespace, None) is None:
            filters = self.get_filters(namespace)
            self._cached[namespace] = dict([(filt.name, filt) for filt 
                                            in filters])
        return self._cached[namespace]

    def get_filters(self, namespace='generic'):
        """
        This runs every for every item to be matched! 
        """
        if namespace in self.filter_namespaces:
            filters = self.filter_namespaces[namespace]
        else:
            filters = []
        plugins = PLUGMAN.process_plugin_data('Filters')
        if plugins:
            plugin_filters = []
            try:
                for plug in plugins:
                    if callable(plug):
                        plug = plug(namespace)
                    if plug:
                        if isinstance(plug, (list, tuple)):
                            for subplug in plug:
                                plugin_filters.append(subplug)
                        else:
                            plugin_filters.append(plug)
            except:
                import traceback
                traceback.print_exc()
            filters += plugin_filters
        return filters

    def add(self, namespace, filt):
        assert(isinstance(namespace, basestring))
        
        if namespace not in self.filter_namespaces:
            self.filter_namespaces[namespace] = []
        self.filter_namespaces[namespace].append(filt)

    def load(self):
        try:
            if os.path.isfile(self.file):
                parser = make_parser()
                parser.setContentHandler(FilterParser(self))
                the_file = open(self.file)
                parser.parse(the_file)
                the_file.close()
        except (IOError,OSError):
            pass
        except SAXParseException:
            print "Parser error"

    def fix(self, line):
        l = line.strip()
        l = l.replace('&', '&amp;')
        l = l.replace('>', '&gt;')
        l = l.replace('<', '&lt;')
        return l.replace('"', '&quot;')

    def save(self):
        f = open(self.file.encode(sys.getfilesystemencoding()), 'w')
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        f.write('<filters>\n')
        for namespace in self.filter_namespaces:
            f.write('<object type="%s">\n' % namespace)
            filter_list = self.filter_namespaces[namespace]
            for the_filter in filter_list:
                f.write('  <filter name="%s"' %self.fix(the_filter.get_name()))
                f.write(' function="%s"' % the_filter.get_logical_op())
                if the_filter.invert:
                    f.write(' invert="1"')
                comment = the_filter.get_comment()
                if comment:
                    f.write(' comment="%s"' % self.fix(comment))
                f.write('>\n')
                for rule in the_filter.get_rules():
                    f.write('    <rule class="%s" use_regex="%s">\n'
                            % (rule.__class__.__name__, rule.use_regex))
                    for value in rule.values():
                        f.write('      <arg value="%s"/>\n' % self.fix(value))
                    f.write('    </rule>\n')
                f.write('  </filter>\n')
            f.write('</object>\n')
        f.write('</filters>\n')
        f.close()
