# -*- python -*-
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2009  Serge Noiraud
# Copyright (C) 2008  Benny Malengier
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
Html Renderer
Can use the Webkit or Gecko ( Mozilla ) library
"""
#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import os
import locale
import urlparse

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger("HtmlRenderer")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# Gramps Modules
#
#-------------------------------------------------------------------------
from gui.views.navigationview import NavigationView
import Bookmarks
import Utils
import constfunc
import config
from const import TEMP_DIR

#-------------------------------------------------------------------------
#
# Functions
#
#-------------------------------------------------------------------------

def get_identity():
    if constfunc.lin():
        platform = "X11"
    elif constfunc.win():
        platform = "Windows"
    elif constfunc.mac():
        platform = "Macintosh"
    else:
        platform = "Unknown"
    (lang_country, modifier ) = locale.getlocale()
    lang = lang_country.replace('_','-')
    #lang += ", " + lang_country.split('_')[0]
    return "Mozilla/5.0 (%s; U; %s) Gramps/3.2" % ( platform, lang)

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
# I think we should set the two following variable in const.py
# They are used only with gtkmozembed.
MOZEMBED_PATH = TEMP_DIR
MOZEMBED_SUBPATH = Utils.get_empty_tempdir('mozembed_gramps')
GEOVIEW_SUBPATH = Utils.get_empty_tempdir('geoview')
NOWEB   = 0
WEBKIT  = 1
MOZILLA = 2
KITNAME = [ "None", "WebKit", "Mozilla" ]
URL_SEP = '/'
MOZJS = '''
user_pref("network.proxy.type", 1);
user_pref("network.proxy.http", %(host)s);
user_pref("network.proxy.http_port", %(port)s);
user_pref("network.proxy.no_proxies_on",
 "127.0.0.1,localhost,localhost
 .localdomain")
user_pref("network.proxy.share_proxy_settings", true);
user_pref("network.http.proxy.pipelining", true);
user_pref("network.http.proxy.keep-alive", true);
user_pref("network.http.proxy.version", 1.1);
user_pref("network.http.sendRefererHeader, 0);
user_pref("general.useragent.extra.firefox, "Mozilla/5.0");
user_pref("general.useragent.locale, %(lang)s);
'''
#-------------------------------------------------------------------------
#
# What Web interfaces ?
#
# We use firstly webkit if it is present. If not, we use gtkmozembed.
# If no web interface is present, we don't register GeoView in the gui.
#-------------------------------------------------------------------------

TOOLKIT = NOWEB

try:
    import webkit
    TOOLKIT = WEBKIT
except:
    pass

try:
    import gtkmozembed
    TOOLKIT += MOZILLA
except:
    pass

#no interfaces present, raise Error so that options for GeoView do not show
if TOOLKIT == NOWEB :
    raise ImportError, 'No GTK html plugin found'
else:
    _LOG.debug("webkit or/and mozilla (gecko) is/are loaded : %d" % TOOLKIT)

def get_toolkits():
    return TOOLKIT

#-------------------------------------------------------------------------
#
# Renderer
#
#-------------------------------------------------------------------------
#class Renderer(object):
class Renderer():
    """
    Renderer renders the webpage. Several backend implementations are 
    possible
    """
    def __init__(self):
        self.window = None

    def get_window(self):
        """
        Returns a container class with the widget that contains browser
        window
        """
        return self.window

    def get_uri(self):
        """
        Get the current url
        """
        raise NotImplementedError

    def show_all(self):
        """
        show all in the main window.
        """
        self.window.show_all()

    def open(self, url):
        """
        open the webpage at url
        """
        raise NotImplementedError

    def refresh(self):
        """
        We need to reload the page.
        """
        raise NotImplementedError

    def go_back(self):
        """
        Go to the previous page.
        """
        self.window.go_back()

    def can_go_back(self):
        """
        is the browser able to go backward ?
        """
        return self.window.can_go_back()

    def go_forward(self):
        """
        Go to the next page.
        """
        self.window.go_forward()

    def can_go_forward(self):
        """
        is the browser able to go forward ?
        """
        return self.window.can_go_forward()

    def get_title(self):
        """
        We need to get the html title page.
        """
        raise NotImplementedError

    def execute_script(self, url):
        """
        execute javascript in the current html page
        """
        raise NotImplementedError

    def page_loaded(self, *args):
        """
        The page is completely loaded.
        """
        raise NotImplementedError

    def set_button_sensitivity(self):
        """
        We must set the back and forward button in the HtmlView class.
        """
        raise NotImplementedError

#-------------------------------------------------------------------------
#
# Renderer with WebKit
#
#-------------------------------------------------------------------------
class RendererWebkit(Renderer):
    """
    Implementation of Renderer with Webkit
    """
    def __init__(self):
        Renderer.__init__(self)
        self.window = webkit.WebView()
        try:
            self.window.set_custom_encoding('utf-8') # needs webkit 1.1.10
        except: # pylint: disable-msg=W0702
            pass
        settings = self.window.get_settings()
        try:
            proxy = os.environ['http_proxy']
            # webkit use libsoup instead of libcurl.
            #if proxy:
            #    settings.set_property("use-proxy", True)
        except: # pylint: disable-msg=W0702
            pass
        try: # needs webkit 1.1.22
            settings.set_property("auto-resize-window", True) 
        except: # pylint: disable-msg=W0702
            pass
        try: # needs webkit 1.1.2
            settings.set_property("enable-private-browsing", True)
        except: # pylint: disable-msg=W0702
            pass
        #settings.set_property("ident-string", get_identity())
        # do we need it ? Yes if webkit avoid to use local files for security
        ## The following available starting from WebKitGTK+ 1.1.13
        #settings.set_property("enable-universal-access-from-file-uris", True)
        self.browser = WEBKIT
        self.title = None
        self.frame = self.window.get_main_frame()
        self.window.connect("document-load-finished", self.page_loaded)
        self.fct = None

    def page_loaded(self, *args):
        """
        We just loaded one page in the browser.
        Set the button sensitivity 
        """
        self.set_button_sensitivity()

    def set_button_sensitivity(self):
        """
        We must set the back and forward button in the HtmlView class.
        """
        self.fct()

    def open(self, url):
        """
        We need to load the page in the browser.
        """
        self.window.open(url)

    def refresh(self):
        """
        We need to reload the page in the browser.
        """
        self.window.reload()

    def execute_script(self, url):
        """
        We need to execute a javascript function into the browser
        """
        self.window.execute_script(url)

    def get_uri(self):
        """
        What is the uri loaded in the browser ?
        """
        return self.window.get_main_frame().get_uri()

#-------------------------------------------------------------------------
#
# The Mozilla or Gecko Renderer class
#
#-------------------------------------------------------------------------
class RendererMozilla(Renderer):
    """
    Implementation of Renderer with gtkmozembed
    """
    def __init__(self):
        Renderer.__init__(self)
        if hasattr(gtkmozembed, 'set_profile_path'):
            set_profile_path = gtkmozembed.set_profile_path
        else:
            set_profile_path = gtkmozembed.gtk_moz_embed_set_profile_path
        set_profile_path(MOZEMBED_PATH, MOZEMBED_SUBPATH)
        self.__set_mozembed_proxy()
        self.window = gtkmozembed.MozEmbed()
        self.browser = MOZILLA
        self.title = None
        self.handler = self.window.connect("net-stop", self.page_loaded)
        self.window.connect("title", self.get_title)
        self.fct = None

    def page_loaded(self, *args):
        """
        We just loaded one page in the browser.
        Set the button sensitivity 
        """
        self.set_button_sensitivity()

    def set_button_sensitivity(self):
        """
        We must set the back and forward button in the HtmlView class.
        """
        self.fct()

    def open(self, url):
        """
        We need to load the page in the browser.
        """
        self.window.load_url(url)

    def get_title(self, *args):
        """
        We need to get the html title page.
        """
        self.title = self.window.get_title()

    def execute_script(self, url):
        """
        We need to execute a javascript function into the browser
        """
        self.window.load_url(url)

    def get_uri(self):
        """
        What is the uri loaded in the browser ?
        """
        return self.window.get_location()

    def refresh(self):
        """
        We need to reload the page in the browser.
        """
        self.window.reload(0)

    def __set_mozembed_proxy(self):
        """
        Try to see if we have some proxy environment variable.
        http_proxy in our case.
        The standard format is : http://[user:password@]proxy:port/
        """
        try:
            proxy = os.environ['http_proxy']
            if proxy:
                host_port = None
                prefs = open(os.path.join(MOZEMBED_SUBPATH,
                                          "prefs.js"),
                             "w+")
                if not os.path.exists(prefs):
                    parts = urlparse.urlparse(proxy)
                    if not parts[0] or parts[0] == 'http':
                        host_port = parts[1]
                        hport = host_port.split(':')
                        host = hport[0].strip()
                        if host:
                            try:
                                port = int(hport[1])
                            except:
                                user = host
                                uprox = hport[1].split('@')
                                password = uprox[0]
                                host = uprox[1]
                                port = int(hport[2])
                    if port and host:
                        port = str(port)
                        (lang_country, modifier ) = locale.getlocale()
                        lang = lang_country.split('_')[0]
                        prefs.write(MOZJS % vars() )
                    prefs.close()
        except:
            try: # trying to remove pref.js in case of proxy change.
                os.remove(os.path.join(MOZEMBED_SUBPATH, "prefs.js"))
            except:
                pass

#-------------------------------------------------------------------------
#
# HtmlView
#
#-------------------------------------------------------------------------
class HtmlView(NavigationView):
    """
    HtmlView is a view showing a top widget with controls, and a bottom part
    with an embedded webbrowser showing a given URL
    """

    def __init__(self, pdata, dbstate, uistate, title=_('HtmlView')):
        NavigationView.__init__(self, title, pdata, dbstate, uistate,
                                dbstate.db.get_bookmarks(), 
                                Bookmarks.PersonBookmarks,
                                nav_group=0
                               )
        self.dbstate = dbstate
        self.back_action = None
        self.forward_action = None
        self.renderer = None
        self.urlfield = ""
        self.htmlfile = ""
        self.filter = gtk.HBox()
        self.table = ""
        self.browser = NOWEB
        self.bootstrap_handler = None
        self.box = None
        self.toolkit = None

        self.additional_uis.append(self.additional_ui())

    def build_widget(self):
        """
        Builds the interface and returns a gtk.Container type that
        contains the interface. This containter will be inserted into
        a gtk.Notebook page.
        """
        self.box = gtk.VBox(False, 4)
        #top widget at the top
        self.box.pack_start(self.top_widget(), False, False, 0 )
        #web page under it in a scrolled window
        self.table = gtk.Table(1, 1, False)
        frames = gtk.HBox(False, 4)
        self.frames = frames
        self.toolkit = TOOLKIT = get_toolkits()
        if   (get_toolkits() == (WEBKIT+MOZILLA)):
            # The two toolkits ( webkit and mozilla ) are available.
            # The user is able to choose what toolkit he will use.
            try:
                # preferences.webkit is useful only in geoview;
                # not in htmlview.
                if self._config.get('preferences.webkit'):
                    TOOLKIT = WEBKIT
                else:
                    TOOLKIT = MOZILLA
            except:
                self.toolkit = "html"
        if self.toolkit == "html":
            _LOG.debug("We are native htmlrenderer.")
            frame = gtk.ScrolledWindow(None, None)
            frame.set_shadow_type(gtk.SHADOW_NONE)
            frame.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            frame.add_with_viewport(self.table)
        else:
            _LOG.debug("We are called by geoview.")
            frame = gtk.Frame()
            frame.set_size_request(100,100)
            frame.add(self.table)
        self.bootstrap_handler = self.box.connect("size-request", 
                                 self.init_parent_signals_for_map)
        self.table.get_parent().set_shadow_type(gtk.SHADOW_NONE)
        self.table.set_row_spacings(1)
        self.table.set_col_spacings(0)
        if   (TOOLKIT == MOZILLA) :
            _LOG.debug("We use gtkmozembed")
            self.renderer = RendererMozilla()
        else:
            _LOG.debug("We use webkit")
            self.renderer = RendererWebkit()
        self.table.add(self.renderer.get_window())
        frames.set_homogeneous(False)
        frames.pack_start(frame, True, True, 0)
        frames.pack_end(self.filter, False, False, 0)
        self.box.pack_start(frames, True, True, 0)
        # this is used to activate the back and forward button
        # from the renderer class.
        self.renderer.fct = lambda: self.set_button_sensitivity
        self.renderer.show_all()
        self.filter.hide()
        #load a welcome html page
        urlhelp = self._create_start_page()
        self.open(urlhelp)
        return self.box

    def top_widget(self):
        """
        The default class gives a widget where user can type an url
        """
        hbox = gtk.HBox(False, 4)
        self.urlfield = gtk.Entry()
        self.urlfield.set_text(config.get("htmlview.start-url"))
        self.urlfield.connect('activate', self._on_activate)
        hbox.pack_start(self.urlfield, True, True, 4)
        button = gtk.Button(stock=gtk.STOCK_APPLY)
        button.connect('clicked', self._on_activate)
        hbox.pack_start(button, False, False, 4)
        return hbox

    def set_button_sensitivity(self):
        """
        Set the backward and forward button in accordance to the browser.
        """
        self.forward_action.set_sensitive(self.renderer.can_go_forward())
        self.back_action.set_sensitive(self.renderer.can_go_back())
        
    def open(self, url):
        """
        open an url
        """
        self.renderer.open(url)

    def go_back(self, button):
        """
        Go to the previous loaded url.
        """
        self.renderer.go_back()
        self.set_button_sensitivity()
        self.external_uri()

    def go_forward(self, button):
        """
        Go to the next loaded url.
        """
        self.renderer.go_forward()
        self.set_button_sensitivity()
        self.external_uri()

    def refresh(self, button):
        """
        Force to reload the page.
        """
        self.renderer.refresh()

    def external_uri(self):
        """
        used to resize or not resize depending on external or local file.
        """
        uri = self.renderer.get_uri()

    def _on_activate(self, nobject):
        """
        Here when we activate the url button.
        """
        url = self.urlfield.get_text()
        if url.find('://') == -1:
            url = 'http://'+ url
        self.open(url)
        
    def build_tree(self):
        """
        Rebuilds the current display. Called from ViewManager
        """
        pass #htmlview is build on click and startup

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        return 'gramps-view'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        return 'gramps-view'

    def additional_ui(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        return '''<ui>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
              <toolitem action="Refresh"/>
            </placeholder>
          </toolbar>
        </ui>'''

    def define_actions(self):
        """
        Required define_actions function for NavigationView. Builds the action
        group information required. 
        """
        NavigationView.define_actions(self)
        HtmlView._define_actions_fw_bw(self)

    def _define_actions_fw_bw(self):
        """
        prepare the forward and backward buttons.
        add the Backward action to handle the Backward button
        accel doesn't work in webkit and gtkmozembed !
        we must do that ...
        """
        self.back_action = gtk.ActionGroup(self.title + '/Back')
        self.back_action.add_actions([
            ('Back', gtk.STOCK_GO_BACK, _("_Back"), 
             "<ALT>Left", _("Go to the previous page in the history"), 
             self.go_back)
            ])
        self._add_action_group(self.back_action)
        # add the Forward action to handle the Forward button
        self.forward_action = gtk.ActionGroup(self.title + '/Forward')
        self.forward_action.add_actions([
            ('Forward', gtk.STOCK_GO_FORWARD, _("_Forward"), 
             "<ALT>Right", _("Go to the next page in the history"), 
             self.go_forward)
            ])
        self._add_action_group(self.forward_action)
        # add the Refresh action to handle the Refresh button
        self._add_action('Refresh', gtk.STOCK_REFRESH, _("_Refresh"), 
                          callback=self.refresh,
                          accel="<Ctl>R",
                          tip=_("Stop and reload the page."))

    def init_parent_signals_for_map(self, widget, event):
        """
        Required to properly bootstrap the signal handlers.
        This handler is connected by build_widget.
        After the outside ViewManager has placed this widget we are
        able to access the parent container.
        """
        pass

    def get_renderer(self):
        """
        return the renderer : Webkit, Mozilla or None
        """
        #return self.browser
        return KITNAME[self.browser]

    def get_toolkit(self):
        """
        return the available toolkits : 1=Webkit, 2=Mozilla or 3=both
        """
        return self.toolkit

    def _create_start_page(self):
        """
        This command creates a default start page, and returns the URL of
        this page.
        """
        tmpdir = GEOVIEW_SUBPATH
        data = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" \
                 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml"  >
         <head>
          <meta http-equiv="content-type" content="text/html; charset=utf-8"/>
          <title>%(title)s</title>
         </head>
         <body >
           <H4>%(content)s</H4>
         </body>
        </html>
        """ % { 'height' : 600,
                'title'  : _('Start page for the Html View'),
                'content': _('Type a webpage address at the top, and hit'
                             ' the execute button to load a webpage in this'
                             ' page\n<br>\n'
                             'For example: <b>http://gramps-project.org</p>')
        }
        filename = os.path.join(tmpdir, 'startpage.html')
        # Now we have two views : Web and Geography, we need to create the
        # startpage only once.
        if not os.path.exists(filename):
            ufd = file(filename, "w+")
            ufd.write(data)
            ufd.close()
        return urlparse.urlunsplit(('file', '',
                                    URL_SEP.join(filename.split(os.sep)),
                                    '', ''))

    def navigation_group(self):
        """
        Return the navigation group.
        """
        return self.nav_group

    def navigation_type(self):
        return 'Person'

    def get_history(self):
        """
        Return the history object.
        """
        _LOG.debug("htmlrenderer : get_history" )
        return self.uistate.get_history(self.navigation_type(),
                                        self.navigation_group())

    def goto_handle(self, handle):
        _LOG.debug("htmlrenderer : gtoto_handle" )
        pass

