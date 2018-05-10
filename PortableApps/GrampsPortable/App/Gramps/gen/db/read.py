#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Nick Hall
# Copyright (C) 2011       Tim G L Lyons
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
Read classes for the GRAMPS databases.
"""
from __future__ import with_statement
#-------------------------------------------------------------------------
#
# libraries
#
#-------------------------------------------------------------------------
import cPickle
import time
import random
import locale
import os
from sys import maxint

import config
if config.get('preferences.use-bsddb3'):
    from bsddb3 import db
else:
    from bsddb import db
from gen.ggettext import gettext as _
import re

import logging

#-------------------------------------------------------------------------
#
# GRAMPS libraries
#
#-------------------------------------------------------------------------
from gen.lib import (MediaObject, Person, Family, Source, Citation, Event,
                     Place, Repository, Note, Tag, GenderStats, Researcher, 
                     NameOriginType)
from gen.db.dbconst import *
from gen.utils.callback import Callback
from gen.db import (BsddbBaseCursor, DbReadBase)
from Utils import create_id
import Errors

LOG = logging.getLogger(DBLOGNAME)
LOG = logging.getLogger(".citation")
#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
from gen.db.dbconst import *

_SIGBASE = ('person', 'family', 'source', 'citation', 
            'event',  'media', 'place', 'repository',
            'reference', 'note', 'tag')

DBERRS      = (db.DBRunRecoveryError, db.DBAccessError, 
               db.DBPageNotFoundError, db.DBInvalidArgError)

#-------------------------------------------------------------------------
#
# Helper functions
#
#-------------------------------------------------------------------------  
def find_surname(key, data):
    """
    Creating a surname from raw data of a person, to use for sort and index
    """
    return __index_surname(data[3][5])

def find_surname_name(key, data):
    """
    Creating a surname from raw name, to use for sort and index
    """
    return __index_surname(data[5])

def __index_surname(surn_list):
    """
    All non pa/matronymic surnames are used in indexing.
    pa/matronymic not as they change for every generation!
    """
    if surn_list:
        surn = " ".join([x[0] for x in surn_list if not (x[3][0] in [
                    NameOriginType.PATRONYMIC, NameOriginType.MATRONYMIC]) ])
    else:
        surn = ""
    return str(surn)
    

#-------------------------------------------------------------------------
#
# class DbBookmarks
#
#-------------------------------------------------------------------------  
class DbBookmarks(object):
    def __init__(self, default=[]):
        self.bookmarks = list(default) # want a copy (not an alias)

    def set(self, new_list):
        self.bookmarks = list(new_list)

    def get(self):
        return self.bookmarks

    def append(self, item):
        self.bookmarks.append(item)

    def append_list(self, blist):
        self.bookmarks += blist

    def remove(self, item):
        self.bookmarks.remove(item)

    def pop(self, item):
        return self.bookmarks.pop(item)

    def insert(self, pos, item):
        self.bookmarks.insert(pos, item)

    def close(self):
        del self.bookmarks

#-------------------------------------------------------------------------
#
# GrampsDBReadCursor
#
#-------------------------------------------------------------------------
class DbReadCursor(BsddbBaseCursor):

    def __init__(self, source, txn=None, **kwargs):
        BsddbBaseCursor.__init__(self, txn=txn, **kwargs)
        self.cursor = source.db.cursor(txn)
        self.source = source

class DbBsddbRead(DbReadBase, Callback):
    """
    Read class for the GRAMPS databases.  Implements methods necessary to read
    the various object classes. Currently, there are nine (9) classes:

    Person, Family, Event, Place, Source, Citation, MediaObject,
    Repository and Note

    For each object class, there are methods to retrieve data in various ways.
    In the methods described below, <object> can be one of person, family,
    event, place, source, media_object, respository or note unless otherwise
    specified.

    .. method:: get_<object>_from_handle()
    
        returns an object given its handle

    .. method:: get_<object>_from_gramps_id()

        returns an object given its gramps id

    .. method:: get_<object>_cursor()

        returns a cursor over an object.  Example use::

            with get_person_cursor() as cursor:
                for handle, person in cursor:
                    # process person object pointed to by the handle

    .. method:: get_<object>_handles()

        returns a list of handles for the object type, optionally sorted
        (for Person, Place, Source and Media objects)

    .. method:: iter_<object>_handles()

        returns an iterator that yields one object handle per call.

    .. method:: iter_<objects>()

        returns an iterator that yields one object per call.
        The objects available are: people, families, events, places,
        sources, media_objects, repositories and notes.

    .. method:: get_<object>_event_types()

        returns a list of all Event types assocated with instances of <object>
        in the database.

    .. method:: get_<object>_attribute_types()

        returns a list of all Event types assocated with instances of <object>
        in the database.
    """

    __signals__ = {}
    # If this is True logging will be turned on.
    try:
        _LOG_ALL = int(os.environ.get('GRAMPS_SIGNAL', "0")) == 1
    except:
        _LOG_ALL = False

    def __init__(self):
        """
        Create a new DbBsddbRead instance. 
        """
        DbReadBase.__init__(self)
        Callback.__init__(self)

        self._tables = {
            'Person':
                {
                "handle_func": self.get_person_from_handle, 
                "gramps_id_func": self.get_person_from_gramps_id,
                "class_func": Person,
                "cursor_func": self.get_person_cursor,
                },
            'Family':
                {
                "handle_func": self.get_family_from_handle, 
                "gramps_id_func": self.get_family_from_gramps_id,
                "class_func": Family,
                "cursor_func": self.get_family_cursor,
                },
            'Source':
                {
                "handle_func": self.get_source_from_handle, 
                "gramps_id_func": self.get_source_from_gramps_id,
                "class_func": Source,
                "cursor_func": self.get_source_cursor,
                },
            'Citation':
                {
                "handle_func": self.get_citation_from_handle, 
                "gramps_id_func": self.get_citation_from_gramps_id,
                "class_func": Citation,
                "cursor_func": self.get_citation_cursor,
                },
            'Event':
                {
                "handle_func": self.get_event_from_handle, 
                "gramps_id_func": self.get_event_from_gramps_id,
                "class_func": Event,
                "cursor_func": self.get_event_cursor,
                },
            'Media':
                {
                "handle_func": self.get_object_from_handle, 
                "gramps_id_func": self.get_object_from_gramps_id,
                "class_func": MediaObject,
                "cursor_func": self.get_media_cursor,
                },
            'Place':
                {
                "handle_func": self.get_place_from_handle, 
                "gramps_id_func": self.get_place_from_gramps_id,
                "class_func": Place,
                "cursor_func": self.get_place_cursor,
                },
            'Repository':
                {
                "handle_func": self.get_repository_from_handle, 
                "gramps_id_func": self.get_repository_from_gramps_id,
                "class_func": Repository,
                "cursor_func": self.get_repository_cursor,
                },
            'Note':
                {
                "handle_func": self.get_note_from_handle, 
                "gramps_id_func": self.get_note_from_gramps_id,
                "class_func": Note,
                "cursor_func": self.get_note_cursor,
                },
            'Tag':
                {
                "handle_func": self.get_tag_from_handle, 
                "gramps_id_func": None,
                "class_func": Tag,
                "cursor_func": self.get_tag_cursor,
                },
            }

        self.set_person_id_prefix('I%04d')
        self.set_object_id_prefix('O%04d')
        self.set_family_id_prefix('F%04d')
        self.set_source_id_prefix('S%04d')
        self.set_citation_id_prefix('C%04d')
        self.set_place_id_prefix('P%04d')
        self.set_event_id_prefix('E%04d')
        self.set_repository_id_prefix('R%04d')
        self.set_note_id_prefix('N%04d')

        self.readonly = False
        self.rand = random.Random(time.time())
        self.smap_index = 0
        self.cmap_index = 0
        self.emap_index = 0
        self.pmap_index = 0
        self.fmap_index = 0
        self.lmap_index = 0
        self.omap_index = 0
        self.rmap_index = 0
        self.nmap_index = 0
        self.db_is_open = False

        self.family_event_names = set()
        self.individual_event_names = set()
        self.individual_attributes = set()
        self.family_attributes = set()
        self.child_ref_types = set()
        self.family_rel_types = set()
        self.event_role_names = set()
        self.name_types = set()
        self.origin_types = set()
        self.repository_types = set()
        self.note_types = set()
        self.source_media_types = set()
        self.url_types = set()
        self.media_attributes = set()

        self.open = 0
        self.genderStats = GenderStats()

        self.undodb    = []
        self.id_trans  = {}
        self.fid_trans = {}
        self.pid_trans = {}
        self.sid_trans = {}
        self.cid_trans = {}
        self.oid_trans = {}
        self.rid_trans = {}
        self.nid_trans = {}
        self.eid_trans = {}
        self.tag_trans = {}
        self.env = None
        self.person_map = {}
        self.family_map = {}
        self.place_map  = {}
        self.source_map = {}
        self.citation_map = {}
        self.repository_map  = {}
        self.note_map = {}
        self.tag_map = {}
        self.media_map  = {}
        self.event_map  = {}
        self.metadata   = {}
        self.name_group = {}
        self.undo_callback = None
        self.redo_callback = None
        self.undo_history_callback = None
        self.modified   = 0

        #self.undoindex  = -1
        #self.translist  = [None] * DBUNDO
        self.abort_possible = True
        #self.undo_history_timestamp = 0
        self.default = None
        self.owner = Researcher()
        self.name_formats = []
        self.bookmarks = DbBookmarks()
        self.family_bookmarks = DbBookmarks()
        self.event_bookmarks = DbBookmarks()
        self.place_bookmarks = DbBookmarks()
        self.source_bookmarks = DbBookmarks()
        self.citation_bookmarks = DbBookmarks()
        self.repo_bookmarks = DbBookmarks()
        self.media_bookmarks = DbBookmarks()
        self.note_bookmarks = DbBookmarks()
        self._bm_changes = 0
        self.path = ""
        self.surname_list = []
        self.txn = None
        self.has_changed = False

    def set_prefixes(self, person, media, family, source, citation, place,
                     event, repository, note):
        self.set_person_id_prefix(person)
        self.set_object_id_prefix(media)
        self.set_family_id_prefix(family)
        self.set_source_id_prefix(source)
        self.set_citation_id_prefix(citation)
        self.set_place_id_prefix(place)
        self.set_event_id_prefix(event)
        self.set_repository_id_prefix(repository)
        self.set_note_id_prefix(note)
        #self.set_tag_id_prefix(tag)

    def version_supported(self):
        """Return True when the file has a supported version."""
        return True

    def get_table_names(self):
        """Return a list of valid table names."""
        return self._tables.keys()

    def get_table_metadata(self, table_name):
        """Return the metadata for a valid table name."""
        if table_name in self._tables:
            return self._tables[table_name]
        return None

    def get_cursor(self, table, *args, **kwargs):
        try:
            return DbReadCursor(table, self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def get_person_cursor(self, *args, **kwargs):
        return self.get_cursor(self.person_map, *args, **kwargs)

    def get_family_cursor(self, *args, **kwargs):
        return self.get_cursor(self.family_map, *args, **kwargs)

    def get_event_cursor(self, *args, **kwargs):
        return self.get_cursor(self.event_map, *args, **kwargs)

    def get_place_cursor(self, *args, **kwargs):
        return self.get_cursor(self.place_map, *args, **kwargs)

    def get_source_cursor(self, *args, **kwargs):
        return self.get_cursor(self.source_map, *args, **kwargs)

    def get_citation_cursor(self, *args, **kwargs):
        return self.get_cursor(self.citation_map, *args, **kwargs)

    def get_media_cursor(self, *args, **kwargs):
        return self.get_cursor(self.media_map, *args, **kwargs)

    def get_repository_cursor(self, *args, **kwargs):
        return self.get_cursor(self.repository_map, *args, **kwargs)

    def get_note_cursor(self, *args, **kwargs):
        return self.get_cursor(self.note_map, *args, **kwargs)

    def get_tag_cursor(self, *args, **kwargs):
        return self.get_cursor(self.tag_map, *args, **kwargs)

    def close(self):
        """
        Close the specified database. 
        
        The method needs to be overridden in the derived class.
        """
        #remove circular dependance
        self.basedb = None
        #remove links to functions
        self.disconnect_all()
        for key in self._tables:
            for subkey in self._tables[key]:
                self._tables[key][subkey] = None
            del self._tables[key][subkey]
            self._tables[key] = None
        del self._tables
##        self.bookmarks = None
##        self.family_bookmarks = None
##        self.event_bookmarks = None
##        self.place_bookmarks = None
##        self.source_bookmarks = None
##        self.citation_bookmarks = None
##        self.repo_bookmarks = None
##        self.media_bookmarks = None
##        self.note_bookmarks = None


    def is_open(self):
        """
        Return 1 if the database has been opened.
        """
        return self.db_is_open

    def request_rebuild(self):
        """
        Notify clients that the data has changed significantly, and that all
        internal data dependent on the database should be rebuilt.
        """
        self.emit('person-rebuild')
        self.emit('family-rebuild')
        self.emit('place-rebuild')
        self.emit('source-rebuild')
        self.emit('citation-rebuild')
        self.emit('media-rebuild')
        self.emit('event-rebuild')
        self.emit('repository-rebuild')
        self.emit('note-rebuild')
        self.emit('tag-rebuild')

    def __find_next_gramps_id(self, prefix, map_index, trans):
        """
        Helper function for find_next_<object>_gramps_id methods
        """
        index = prefix % map_index
        while trans.get(str(index), txn=self.txn) is not None:
            map_index += 1
            index = prefix % map_index
        map_index += 1
        return (map_index, index)
        
    def find_next_person_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Person object based off the 
        person ID prefix.
        """
        self.pmap_index, gid = self.__find_next_gramps_id(self.person_prefix,
                                          self.pmap_index, self.id_trans)
        return gid

    def find_next_place_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Place object based off the 
        place ID prefix.
        """
        self.lmap_index, gid = self.__find_next_gramps_id(self.place_prefix,
                                          self.lmap_index, self.pid_trans)
        return gid

    def find_next_event_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Event object based off the 
        event ID prefix.
        """
        self.emap_index, gid = self.__find_next_gramps_id(self.event_prefix,
                                          self.emap_index, self.eid_trans)
        return gid

    def find_next_object_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a MediaObject object based
        off the media object ID prefix.
        """
        self.omap_index, gid = self.__find_next_gramps_id(self.mediaobject_prefix,
                                          self.omap_index, self.oid_trans)
        return gid

    def find_next_source_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Source object based off the 
        source ID prefix.
        """
        self.smap_index, gid = self.__find_next_gramps_id(self.source_prefix,
                                          self.smap_index, self.sid_trans)
        return gid

    def find_next_citation_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Source object based off the 
        source ID prefix.
        """
        self.cmap_index, gid = self.__find_next_gramps_id(self.citation_prefix,
                                          self.cmap_index, self.cid_trans)
        return gid

    def find_next_family_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Family object based off the 
        family ID prefix.
        """
        self.fmap_index, gid = self.__find_next_gramps_id(self.family_prefix,
                                          self.fmap_index, self.fid_trans)
        return gid

    def find_next_repository_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Respository object based 
        off the repository ID prefix.
        """
        self.rmap_index, gid = self.__find_next_gramps_id(self.repository_prefix,
                                          self.rmap_index, self.rid_trans)
        return gid

    def find_next_note_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Note object based off the 
        note ID prefix.
        """
        self.nmap_index, gid = self.__find_next_gramps_id(self.note_prefix,
                                          self.nmap_index, self.nid_trans)
        return gid

    def get_from_handle(self, handle, class_type, data_map):
        data = data_map.get(str(handle))
        if data:
            newobj = class_type()
            newobj.unserialize(data)
            return newobj
        return None

    def get_from_name_and_handle(self, table_name, handle):
        """
        Returns a gen.lib object (or None) given table_name and
        handle.

        Examples:

        >>> self.get_from_name_and_handle("Person", "a7ad62365bc652387008")
        >>> self.get_from_name_and_handle("Media", "c3434653675bcd736f23")
        """
        if table_name in self._tables:
            return self._tables[table_name]["handle_func"](handle)
        return None

    def get_from_name_and_gramps_id(self, table_name, gramps_id):
        """
        Returns a gen.lib object (or None) given table_name and
        gramps ID.

        Examples:

        >>> self.get_from_name_and_gramps_id("Person", "I00002")
        >>> self.get_from_name_and_gramps_id("Family", "F056")
        >>> self.get_from_name_and_gramps_id("Media", "M00012")
        """
        if table_name in self._tables:
            return self._tables[table_name]["gramps_id_func"](gramps_id)
        return None

    def get_person_from_handle(self, handle):
        """
        Find a Person in the database from the passed handle.
        
        If no such Person exists, None is returned.
        """
        return self.get_from_handle(handle, Person, self.person_map)

    def get_source_from_handle(self, handle):
        """
        Find a Source in the database from the passed handle.
        
        If no such Source exists, None is returned.
        """
        return self.get_from_handle(handle, Source, self.source_map)

    def get_citation_from_handle(self, handle):
        """
        Find a Citation in the database from the passed handle.
        
        If no such Citation exists, None is returned.
        """
        return self.get_from_handle(handle, Citation, self.citation_map)

    def get_object_from_handle(self, handle):
        """
        Find an Object in the database from the passed handle.
        
        If no such Object exists, None is returned.
        """
        return self.get_from_handle(handle, MediaObject, self.media_map)

    def get_place_from_handle(self, handle):
        """
        Find a Place in the database from the passed handle.
        
        If no such Place exists, None is returned.
        """
        return self.get_from_handle(handle, Place, self.place_map)

    def get_event_from_handle(self, handle):
        """
        Find a Event in the database from the passed handle.
        
        If no such Event exists, None is returned.
        """
        return self.get_from_handle(handle, Event, self.event_map)

    def get_family_from_handle(self, handle):
        """
        Find a Family in the database from the passed handle.
        
        If no such Family exists, None is returned.
        """
        return self.get_from_handle(handle, Family, self.family_map)

    def get_repository_from_handle(self, handle):
        """
        Find a Repository in the database from the passed handle.
        
        If no such Repository exists, None is returned.
        """
        return self.get_from_handle(handle, Repository, self.repository_map)

    def get_note_from_handle(self, handle):
        """
        Find a Note in the database from the passed handle.
        
        If no such Note exists, None is returned.
        """
        return self.get_from_handle(handle, Note, self.note_map)

    def get_tag_from_handle(self, handle):
        """
        Find a Tag in the database from the passed handle.
        
        If no such Tag exists, None is returned.
        """
        return self.get_from_handle(handle, Tag, self.tag_map)

    def __get_obj_from_gramps_id(self, val, tbl, class_, prim_tbl):
        if isinstance(tbl, dict): return None ## trying to get object too early
        try:
            data = tbl.get(str(val), txn=self.txn)
            if data is not None:
                obj = class_()
                ### FIXME: this is a dirty hack that works without no
                ### sensible explanation. For some reason, for a readonly
                ### database, secondary index returns a primary table key
                ### corresponding to the data, not the data.
                if self.readonly:
                    tuple_data = prim_tbl.get(data, txn=self.txn)
                else:
                    tuple_data = cPickle.loads(data)
                obj.unserialize(tuple_data)
                return obj
            else:
                return None
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)

    def get_person_from_gramps_id(self, val):
        """
        Find a Person in the database from the passed gramps' ID.
        
        If no such Person exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.id_trans, Person,
                                             self.person_map)

    def get_family_from_gramps_id(self, val):
        """
        Find a Family in the database from the passed gramps' ID.
        
        If no such Family exists, None is return.
        """
        return self.__get_obj_from_gramps_id(val, self.fid_trans, Family,
                                             self.family_map)
    
    def get_event_from_gramps_id(self, val):
        """
        Find an Event in the database from the passed gramps' ID.
        
        If no such Family exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.eid_trans, Event,
                                             self.event_map)

    def get_place_from_gramps_id(self, val):
        """
        Find a Place in the database from the passed gramps' ID.
        
        If no such Place exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.pid_trans, Place,
                                             self.place_map)

    def get_source_from_gramps_id(self, val):
        """
        Find a Source in the database from the passed gramps' ID.
        
        If no such Source exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.sid_trans, Source,
                                              self.source_map)

    def get_citation_from_gramps_id(self, val):
        """
        Find a Citation in the database from the passed gramps' ID.
        
        If no such Citation exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.cid_trans, Citation,
                                              self.citation_map)

    def get_object_from_gramps_id(self, val):
        """
        Find a MediaObject in the database from the passed gramps' ID.
        
        If no such MediaObject exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.oid_trans, MediaObject,
                                              self.media_map)

    def get_repository_from_gramps_id(self, val):
        """
        Find a Repository in the database from the passed gramps' ID.
        
        If no such Repository exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.rid_trans, Repository,
                                              self.repository_map)

    def get_note_from_gramps_id(self, val):
        """
        Find a Note in the database from the passed gramps' ID.
        
        If no such Note exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.nid_trans, Note,
                                              self.note_map)

    def get_tag_from_name(self, val):
        """
        Find a Tag in the database from the passed Tag name.
        
        If no such Tag exists, None is returned.
        """
        return self.__get_obj_from_gramps_id(val, self.tag_trans, Tag,
                                              self.tag_map)
 
    def get_name_group_mapping(self, surname):
        """
        Return the default grouping name for a surname.
        """
        return unicode(self.name_group.get(str(surname), surname))

    def get_name_group_keys(self):
        """
        Return the defined names that have been assigned to a default grouping.
        """
        return map(unicode, self.name_group.keys())

    def has_name_group_key(self, name):
        """
        Return if a key exists in the name_group table.
        """
        # The use of has_key seems allright because there is no write lock
        # on the name_group table when this is called.
        return self.name_group.has_key(str(name))

    def get_number_of_records(self, table):
        if not self.db_is_open:
            return 0
        if self.txn is None:
            return len(table)
        else:
            return table.stat(flags=db.DB_FAST_STAT, txn=self.txn)['nkeys']

    def get_number_of_people(self):
        """
        Return the number of people currently in the database.
        """
        return self.get_number_of_records(self.person_map)

    def get_number_of_families(self):
        """
        Return the number of families currently in the database.
        """
        return self.get_number_of_records(self.family_map)

    def get_number_of_events(self):
        """
        Return the number of events currently in the database.
        """
        return self.get_number_of_records(self.event_map)

    def get_number_of_places(self):
        """
        Return the number of places currently in the database.
        """
        return self.get_number_of_records(self.place_map)

    def get_number_of_sources(self):
        """
        Return the number of sources currently in the database.
        """
        return self.get_number_of_records(self.source_map)

    def get_number_of_citations(self):
        """
        Return the number of citations currently in the database.
        """
        return self.get_number_of_records(self.citation_map)

    def get_number_of_media_objects(self):
        """
        Return the number of media objects currently in the database.
        """
        return self.get_number_of_records(self.media_map)

    def get_number_of_repositories(self):
        """
        Return the number of source repositories currently in the database.
        """
        return self.get_number_of_records(self.repository_map)

    def get_number_of_notes(self):
        """
        Return the number of notes currently in the database.
        """
        return self.get_number_of_records(self.note_map)

    def get_number_of_tags(self):
        """
        Return the number of tags currently in the database.
        """
        return self.get_number_of_records(self.tag_map)

    def is_empty(self):
        """
        Return true if there are no [primary] records in the database
        """
        for obj_map in [self.person_map, self.family_map, self.event_map,
                        self.place_map, self.source_map, self.citation_map,
                        self.media_map, self.repository_map, self.note_map,
                        self.tag_map]:
            if self.get_number_of_records(obj_map) > 0:
                return False
            return True

    def all_handles(self, table):
        return table.keys(txn=self.txn)
        
    def get_person_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Person in
        the database. 
        
        If sort_handles is True, the list is sorted by surnames.
        """
        if self.db_is_open:
            handle_list = self.all_handles(self.person_map)
            if sort_handles:
                handle_list.sort(key=self.__sortbyperson_key)
            return handle_list
        return []

    def get_place_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Place in
        the database. 
        
        If sort_handles is True, the list is sorted by Place title.
        """

        if self.db_is_open:
            handle_list = self.all_handles(self.place_map)
            if sort_handles:
                handle_list.sort(key=self.__sortbyplace_key)
            return handle_list
        return []

    def get_source_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Source in
        the database.
        
         If sort_handles is True, the list is sorted by Source title.
        """
        if self.db_is_open:
            handle_list = self.all_handles(self.source_map)
            if sort_handles:
                handle_list.sort(key=self.__sortbysource_key)
            return handle_list
        return []
        
    def get_citation_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Citation in
        the database.
        
         If sort_handles is True, the list is sorted by Citation Volume/Page.
        """
        if self.db_is_open:
            handle_list = self.all_handles(self.citation_map)
            if sort_handles:
                handle_list.sort(key=self.__sortbycitation_key)
            return handle_list
        return []
        
    def get_media_object_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each MediaObject in
        the database. 
        
        If sort_handles is True, the list is sorted by title.
        """
        if self.db_is_open:
            handle_list = self.all_handles(self.media_map)
            if sort_handles:
                handle_list.sort(key=self.__sortbymedia_key)
            return handle_list
        return []
        
    def get_event_handles(self):
        """
        Return a list of database handles, one handle for each Event in the 
        database. 
        """
        if self.db_is_open:
            return self.all_handles(self.event_map)
        return []
        
    def get_family_handles(self):
        """
        Return a list of database handles, one handle for each Family in
        the database.
        """
        if self.db_is_open:
            return self.all_handles(self.family_map)
        return []
        
    def get_repository_handles(self):
        """
        Return a list of database handles, one handle for each Repository in
        the database.
        """
        if self.db_is_open:
            return self.all_handles(self.repository_map)
        return []
        
    def get_note_handles(self):
        """
        Return a list of database handles, one handle for each Note in the 
        database.
        """
        if self.db_is_open:
            return self.all_handles(self.note_map)
        return []

    def get_tag_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Tag in
        the database.
        
         If sort_handles is True, the list is sorted by Tag name.
        """
        if self.db_is_open:
            handle_list = self.all_handles(self.tag_map)
            if sort_handles:
                handle_list.sort(key=self.__sortbytag_key)
            return handle_list
        return []

    def _f(curs_):
        """
        Closure that returns an iterator over handles in the database.
        """
        def g(self):
            with curs_(self) as cursor:
                for key, data in cursor:
                    yield key
        return g

    # Use closure to define iterators for each primary object type

    iter_person_handles       = _f(get_person_cursor)
    iter_family_handles       = _f(get_family_cursor)
    iter_event_handles        = _f(get_event_cursor)
    iter_place_handles        = _f(get_place_cursor)
    iter_source_handles       = _f(get_source_cursor)
    iter_citation_handles     = _f(get_citation_cursor)
    iter_media_object_handles = _f(get_media_cursor)
    iter_repository_handles   = _f(get_repository_cursor)
    iter_note_handles         = _f(get_note_cursor)
    iter_tag_handles          = _f(get_tag_cursor)
    del _f
    
    def _f(curs_, obj_):
        """
        Closure that returns an iterator over objects in the database.
        """
        def g(self):
            with curs_(self) as cursor:
                for key, data in cursor:
                    obj = obj_()
                    obj.unserialize(data)
                    yield obj
        return g

    # Use closure to define iterators for each primary object type
    
    iter_people        = _f(get_person_cursor, Person)
    iter_families      = _f(get_family_cursor, Family)
    iter_events        = _f(get_event_cursor, Event)
    iter_places        = _f(get_place_cursor, Place)
    iter_sources       = _f(get_source_cursor, Source)
    iter_citations     = _f(get_citation_cursor, Citation)
    iter_media_objects = _f(get_media_cursor, MediaObject)
    iter_repositories  = _f(get_repository_cursor, Repository)
    iter_notes         = _f(get_note_cursor, Note)
    iter_tags          = _f(get_tag_cursor, Tag)
    del _f

    def get_gramps_ids(self, obj_key):
        key2table = {
            PERSON_KEY:     self.id_trans, 
            FAMILY_KEY:     self.fid_trans, 
            SOURCE_KEY:     self.sid_trans, 
            CITATION_KEY:   self.cid_trans, 
            EVENT_KEY:      self.eid_trans, 
            MEDIA_KEY:      self.oid_trans, 
            PLACE_KEY:      self.pid_trans, 
            REPOSITORY_KEY: self.rid_trans, 
            NOTE_KEY:       self.nid_trans, 
            }

        table = key2table[obj_key]
        return table.keys()

    def has_gramps_id(self, obj_key, gramps_id):
        key2table = {
            PERSON_KEY:     self.id_trans, 
            FAMILY_KEY:     self.fid_trans, 
            SOURCE_KEY:     self.sid_trans, 
            CITATION_KEY:   self.cid_trans, 
            EVENT_KEY:      self.eid_trans, 
            MEDIA_KEY:      self.oid_trans, 
            PLACE_KEY:      self.pid_trans, 
            REPOSITORY_KEY: self.rid_trans, 
            NOTE_KEY:       self.nid_trans, 
            }

        table = key2table[obj_key]
        #return str(gramps_id) in table
        return table.get(str(gramps_id), txn=self.txn) is not None

    def find_initial_person(self):
        person = self.get_default_person()
        if not person:
            the_ids = self.get_gramps_ids(PERSON_KEY)
            if the_ids:
                person = self.get_person_from_gramps_id(min(the_ids))
        return person

    @staticmethod
    def _validated_id_prefix(val, default):
        if isinstance(val, basestring) and val:
            try:
                str_ = val % 1
            except TypeError:           # missing conversion specifier
                prefix_var = val + "%d"
            except ValueError:          # incomplete format
                prefix_var = default+"%04d"
            else:
                prefix_var = val        # OK as given
        else:
            prefix_var = default+"%04d" # not a string or empty string
        return prefix_var

    @staticmethod
    def __id2user_format(id_pattern):
        """
        Return a method that accepts a Gramps ID and adjusts it to the users
        format.
        """
        pattern_match = re.match(r"(.*)%[0 ](\d+)[diu]$", id_pattern)
        if pattern_match:
            str_prefix = pattern_match.group(1)
            nr_width = pattern_match.group(2)
            def closure_func(gramps_id):
                if gramps_id and gramps_id.startswith(str_prefix):
                    id_number = gramps_id[len(str_prefix):]
                    if id_number.isdigit():
                        id_value = int(id_number, 10)
                        if len(str(id_value)) > nr_width:
                            # The ID to be imported is too large to fit in the
                            # users format. For now just create a new ID,
                            # because that is also what happens with IDs that
                            # are identical to IDs already in the database. If
                            # the problem of colliding import and already
                            # present IDs is solved the code here also needs
                            # some solution.
                            gramps_id = id_pattern % 1
                        else:
                            gramps_id = id_pattern % id_value
                return gramps_id
        else:
            def closure_func(gramps_id):
                return gramps_id
        return closure_func

    def set_person_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Person ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as I%d or I%04d.
        """
        self.person_prefix = self._validated_id_prefix(val, "I")
        self.id2user_format = self.__id2user_format(self.person_prefix)

    def set_source_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Source ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as S%d or S%04d.
        """
        self.source_prefix = self._validated_id_prefix(val, "S")
        self.sid2user_format = self.__id2user_format(self.source_prefix)
            
    def set_citation_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Citation ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as C%d or C%04d.
        """
        self.citation_prefix = self._validated_id_prefix(val, "C")
        self.cid2user_format = self.__id2user_format(self.citation_prefix)
            
    def set_object_id_prefix(self, val):
        """
        Set the naming template for GRAMPS MediaObject ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as O%d or O%04d.
        """
        self.mediaobject_prefix = self._validated_id_prefix(val, "O")
        self.oid2user_format = self.__id2user_format(self.mediaobject_prefix)

    def set_place_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Place ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as P%d or P%04d.
        """
        self.place_prefix = self._validated_id_prefix(val, "P")
        self.pid2user_format = self.__id2user_format(self.place_prefix)

    def set_family_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Family ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as F%d
        or F%04d.
        """
        self.family_prefix = self._validated_id_prefix(val, "F")
        self.fid2user_format = self.__id2user_format(self.family_prefix)

    def set_event_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Event ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as E%d or E%04d.
        """
        self.event_prefix = self._validated_id_prefix(val, "E")
        self.eid2user_format = self.__id2user_format(self.event_prefix)

    def set_repository_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Repository ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as R%d or R%04d.
        """
        self.repository_prefix = self._validated_id_prefix(val, "R")
        self.rid2user_format = self.__id2user_format(self.repository_prefix)

    def set_note_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Note ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as N%d or N%04d.
        """
        self.note_prefix = self._validated_id_prefix(val, "N")
        self.nid2user_format = self.__id2user_format(self.note_prefix)

    def set_undo_callback(self, callback):
        """
        Define the callback function that is called whenever an undo operation
        is executed. 
        
        The callback function receives a single argument that is a text string 
        that defines the operation.
        """
        self.undo_callback = callback

    def set_redo_callback(self, callback):
        """
        Define the callback function that is called whenever an redo operation
        is executed. 
        
        The callback function receives a single argument that is a text string 
        that defines the operation.
        """
        self.redo_callback = callback

    def get_surname_list(self):
        """
        Return the list of locale-sorted surnames contained in the database.
        """
        return self.surname_list

    def get_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.bookmarks

    def get_family_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.family_bookmarks

    def get_event_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.event_bookmarks

    def get_place_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.place_bookmarks

    def get_source_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.source_bookmarks

    def get_citation_bookmarks(self):
        """Return the list of Citation handles in the bookmarks."""
        return self.citation_bookmarks

    def get_media_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.media_bookmarks

    def get_repo_bookmarks(self):
        """Return the list of Person handles in the bookmarks."""
        return self.repo_bookmarks

    def get_note_bookmarks(self):
        """Return the list of Note handles in the bookmarks."""
        return self.note_bookmarks

    def set_researcher(self, owner):
        """Set the information about the owner of the database."""
        self.owner.set_from(owner)

    def get_researcher(self):
        """
        Return the Researcher instance, providing information about the owner 
        of the database.
        """
        return self.owner

    def get_default_person(self):
        """Return the default Person of the database."""
        person = self.get_person_from_handle(self.get_default_handle())
        if person:
            return person
        elif (self.metadata is not None) and (not self.readonly):
            self.metadata['default'] = None
        return None

    def get_default_handle(self):
        """Return the default Person of the database."""
        if self.metadata is not None:
            return self.metadata.get('default')
        return None

    def get_save_path(self):
        """Return the save path of the file, or "" if one does not exist."""
        return self.path

    def set_save_path(self, path):
        """Set the save path for the database."""
        self.path = path

    def get_person_event_types(self):
        """
        Return a list of all Event types assocated with Person instances in 
        the database.
        """
        return list(self.individual_event_names)

    def get_person_attribute_types(self):
        """
        Return a list of all Attribute types assocated with Person instances 
        in the database.
        """
        return list(self.individual_attributes)

    def get_family_attribute_types(self):
        """
        Return a list of all Attribute types assocated with Family instances 
        in the database.
        """
        return list(self.family_attributes)

    def get_family_event_types(self):
        """
        Return a list of all Event types assocated with Family instances in 
        the database.
        """
        return list(self.family_event_names)

    def get_media_attribute_types(self):
        """
        Return a list of all Attribute types assocated with Media and MediaRef 
        instances in the database.
        """
        return list(self.media_attributes)

    def get_family_relation_types(self):
        """
        Return a list of all relationship types assocated with Family
        instances in the database.
        """
        return list(self.family_rel_types)

    def get_child_reference_types(self):
        """
        Return a list of all child reference types assocated with Family
        instances in the database.
        """
        return list(self.child_ref_types)

    def get_event_roles(self):
        """
        Return a list of all custom event role names assocated with Event
        instances in the database.
        """
        return list(self.event_role_names)

    def get_name_types(self):
        """
        Return a list of all custom names types assocated with Person
        instances in the database.
        """
        return list(self.name_types)

    def get_origin_types(self):
        """
        Return a list of all custom origin types assocated with Person/Surname
        instances in the database.
        """
        return list(self.origin_types)

    def get_repository_types(self):
        """
        Return a list of all custom repository types assocated with Repository 
        instances in the database.
        """
        return list(self.repository_types)

    def get_note_types(self):
        """
        Return a list of all custom note types assocated with Note instances 
        in the database.
        """
        return list(self.note_types)

    def get_source_media_types(self):
        """
        Return a list of all custom source media types assocated with Source 
        instances in the database.
        """
        return list(self.source_media_types)

    def get_url_types(self):
        """
        Return a list of all custom names types assocated with Url instances 
        in the database.
        """
        return list(self.url_types)

    def __log_error(self):
        pass            

    def __get_raw_data(self, table, handle):
        """
        Helper method for get_raw_<object>_data methods
        """
        try:
            return table.get(str(handle), txn=self.txn)
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
    
    def get_raw_person_data(self, handle):
        return self.__get_raw_data(self.person_map, handle)

    def get_raw_family_data(self, handle):
        return self.__get_raw_data(self.family_map, handle)

    def get_raw_object_data(self, handle):
        return self.__get_raw_data(self.media_map, handle)

    def get_raw_place_data(self, handle):
        return self.__get_raw_data(self.place_map, handle)

    def get_raw_event_data(self, handle):
        return self.__get_raw_data(self.event_map, handle)

    def get_raw_source_data(self, handle):
        return self.__get_raw_data(self.source_map, handle)

    def get_raw_citation_data(self, handle):
        return self.__get_raw_data(self.citation_map, handle)

    def get_raw_repository_data(self, handle):
        return self.__get_raw_data(self.repository_map, handle)

    def get_raw_note_data(self, handle):
        return self.__get_raw_data(self.note_map, handle)

    def get_raw_tag_data(self, handle):
        return self.__get_raw_data(self.tag_map, handle)

    def __has_handle(self, table, handle):
        """
        Helper function for has_<object>_handle methods
        """
        try:
            return table.get(str(handle), txn=self.txn) is not None
        except DBERRS, msg:
            self.__log_error()
            raise Errors.DbError(msg)
        
    def has_person_handle(self, handle):
        """
        Return True if the handle exists in the current Person database.
        """
        return self.__has_handle(self.person_map, handle)

    def has_family_handle(self, handle):            
        """
        Return True if the handle exists in the current Family database.
        """
        return self.__has_handle(self.family_map, handle)

    def has_object_handle(self, handle):
        """
        Return True if the handle exists in the current MediaObjectdatabase.
        """
        return self.__has_handle(self.media_map, handle)

    def has_repository_handle(self, handle):
        """
        Return True if the handle exists in the current Repository database.
        """
        return self.__has_handle(self.repository_map, handle)

    def has_note_handle(self, handle):
        """
        Return True if the handle exists in the current Note database.
        """
        return self.__has_handle(self.note_map, handle)

    def has_event_handle(self, handle):
        """
        Return True if the handle exists in the current Event database.
        """
        return self.__has_handle(self.event_map, handle)

    def has_place_handle(self, handle):
        """
        Return True if the handle exists in the current Place database.
        """
        return self.__has_handle(self.place_map, handle)

    def has_source_handle(self, handle):
        """
        Return True if the handle exists in the current Source database.
        """
        return self.__has_handle(self.source_map, handle)

    def has_citation_handle(self, handle):
        """
        Return True if the handle exists in the current Citation database.
        """
        return self.__has_handle(self.citation_map, handle)

    def has_tag_handle(self, handle):
        """
        Return True if the handle exists in the current Tag database.
        """
        return self.__has_handle(self.tag_map, handle)

    def __sortbyperson_key(self, person):
        return locale.strxfrm(find_surname(str(person), 
                                           self.person_map.get(str(person))))

    def __sortbyplace(self, first, second):
        return locale.strcoll(self.place_map.get(str(first))[2], 
                              self.place_map.get(str(second))[2])

    def __sortbyplace_key(self, place):
        return locale.strxfrm(self.place_map.get(str(place))[2])

    def __sortbysource(self, first, second):
        source1 = unicode(self.source_map[str(first)][2])
        source2 = unicode(self.source_map[str(second)][2])
        return locale.strcoll(source1, source2)
        
    def __sortbysource_key(self, key):
        source = unicode(self.source_map[str(key)][2])
        return locale.strxfrm(source)

    def __sortbycitation(self, first, second):
        citation1 = unicode(self.citation_map[str(first)][3])
        citation2 = unicode(self.citation_map[str(second)][3])
        return locale.strcoll(citation1, citation2)
        
    def __sortbycitation_key(self, key):
        citation = unicode(self.citation_map[str(key)][3])
        return locale.strxfrm(citation)

    def __sortbymedia(self, first, second):
        media1 = self.media_map[str(first)][4]
        media2 = self.media_map[str(second)][4]
        return locale.strcoll(media1, media2)

    def __sortbymedia_key(self, key):
        media = self.media_map[str(key)][4]
        return locale.strxfrm(media)

    def __sortbytag(self, first, second):
        tag1 = self.tag_map[str(first)][1]
        tag2 = self.tag_map[str(second)][1]
        return locale.strcoll(tag1, tag2)

    def __sortbytag_key(self, key):
        tag = self.tag_map[str(key)][1]
        return locale.strxfrm(tag)

    def set_mediapath(self, path):
        """Set the default media path for database, path should be utf-8."""
        if (self.metadata is not None) and (not self.readonly):
            self.metadata['mediapath'] = path

    def get_mediapath(self):
        """Return the default media path of the database."""
        if self.metadata is not None:
            return self.metadata.get('mediapath', None)
        return None

    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.
        
        Returns an interator over alist of (class_name, handle) tuples.

        :param handle: handle of the object to search for.
        :type handle: database handle
        :param include_classes: list of class names to include in the results.
            Defaults to None, which includes all classes.
        :type include_classes: list of class names
        
        This default implementation does a sequencial scan through all
        the primary object databases and is very slow. Backends can
        override this method to provide much faster implementations that
        make use of additional capabilities of the backend.

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use::

            result_list = list(find_backlink_handles(handle))
        """
        assert False, "read:find_backlink_handles -- shouldn't get here!!!"
        # Make a dictionary of the functions and classes that we need for
        # each of the primary object tables.
        primary_tables = {
            'Person': {
                'cursor_func': self.get_person_cursor, 
                'class_func': Person,
                }, 
            'Family': {
                'cursor_func': self.get_family_cursor, 
                'class_func': Family,
                }, 
            'Event': {
                'cursor_func': self.get_event_cursor, 
                'class_func': Event,
                }, 
            'Place': {
                'cursor_func': self.get_place_cursor, 
                'class_func': Place,
                }, 
            'Source': {
                'cursor_func': self.get_source_cursor, 
                'class_func': Source,
                }, 
            'Citation': {
                'cursor_func': self.get_citation_cursor, 
                'class_func': Citation,
                }, 
            'MediaObject': {
                'cursor_func': self.get_media_cursor, 
                'class_func': MediaObject,
                }, 
            'Repository': {
                'cursor_func': self.get_repository_cursor, 
                'class_func': Repository,
                },
            'Note':   {
                'cursor_func': self.get_note_cursor, 
                'class_func': Note,
                },
            'Tag':   {
                'cursor_func': self.get_tag_cursor, 
                'class_func': Tag,
                },
            }

        # Find which tables to iterate over
        if (include_classes is None):
            the_tables = primary_tables.keys()
        else:
            the_tables = include_classes
        
        # Now we use the functions and classes defined above to loop through
        # each of the existing primary object tables
        for primary_table_name, funcs in the_tables.iteritems():
            with funcs['cursor_func']() as cursor:

            # Grab the real object class here so that the lookup does
            # not happen inside the main loop.
                class_func = funcs['class_func']
                for found_handle, val in cursor:
                    obj = class_func()
                    obj.unserialize(val)

                    # Now we need to loop over all object types
                    # that have been requests in the include_classes list
                    for classname in primary_tables:               
                        if obj.has_handle_reference(classname, handle):
                            yield (primary_table_name, found_handle)
        return

    def report_bm_change(self):
        """
        Add 1 to the number of bookmark changes during this session.
        """
        self._bm_changes += 1

    def db_has_bm_changes(self):
        """
        Return whethere there were bookmark changes during the session.
        """
        return self._bm_changes > 0

    def get_dbid(self):
        """
        In BSDDB, we use the file directory name as the unique ID for
        this database on this computer.
        """
        return None

    def get_dbname(self):
        """
        In BSDDB, the database is in a text file at the path
        """
        filepath = os.path.join(self.path, "name.txt")
        try:
            name_file = open(filepath, "r")
            name = name_file.readline().strip()
            name_file.close()
        except (OSError, IOError), msg:
            self.__log_error()
            name = None
        return name
