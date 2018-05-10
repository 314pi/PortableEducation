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

import gtk

try:
    from gnomevfs import mime_get_short_list_applications, \
         mime_get_description, get_mime_type, mime_get_default_application
except:
    from gnome.vfs import mime_get_short_list_applications, \
         mime_get_description, get_mime_type, mime_get_default_application
    
from gen.ggettext import gettext as _

def get_description(type):
    """Return the description of the specified mime type."""
    try:
        return mime_get_description(type)
    except:
        return _("unknown")

def get_type(file):
    """Return the mime type of the specified file."""
    try:
        return get_mime_type(file)
    except:
        return _('unknown')

def mime_type_is_defined(type):
    """
    Return True if a description for a mime type exists.
    """
    try:
        mime_get_description(type)
        return True
    except:
        return False
 
 #-------------------------------------------------------------------------
#
# private functions
#
#-------------------------------------------------------------------------
def _is_good_command(cmd):
    """
    We don't know what to do with certain substitution values.
    If we find one, skip the command.
    """
    for sub in [ "%m", "%i", "%c" ]:
        if cmd.find(sub) != -1:
            return False
    return True