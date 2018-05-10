#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

# $Id$

# Written by Alex Roitman

"Rebuild reference map tables"

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".RebuildRefMap")

#-------------------------------------------------------------------------
#
# gtk modules
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gui.plug import tool
from QuestionDialog import OkDialog
from gen.updatecallback import UpdateCallback

#-------------------------------------------------------------------------
#
# runTool
#
#-------------------------------------------------------------------------
class RebuildRefMap(tool.Tool, UpdateCallback):

    def __init__(self, dbstate, uistate, options_class, name, callback=None):
        
        tool.Tool.__init__(self, dbstate, options_class, name)

        if self.db.readonly:
            return

        self.db.disable_signals()
        if uistate:
            self.callback = uistate.pulse_progressbar
            uistate.set_busy_cursor(1)
            uistate.progress.show()
            uistate.push_message(dbstate, _("Rebuilding reference maps..."))
        else:
            self.callback = None
            print "Rebuilding reference maps..."
            
        UpdateCallback.__init__(self, self.callback)
        self.set_total(6)
        self.db.reindex_reference_map(self.update)
        self.reset()

        if uistate:
            uistate.set_busy_cursor(0)
            uistate.progress.hide()
            OkDialog(_("Reference maps rebuilt"),
                     _('All reference maps have been rebuilt.'),
                     parent=uistate.window)
        else:
            print "All reference maps have been rebuilt."
        self.db.enable_signals()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class RebuildRefMapOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        tool.ToolOptions.__init__(self, name,person_id)
