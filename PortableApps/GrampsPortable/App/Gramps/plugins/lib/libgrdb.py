#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
Base class for the GRAMPS databases before version 3.0.
All database interfaces should inherit from this class.
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

import logging
LOG = logging.getLogger(".Db")

#-------------------------------------------------------------------------
#
# GRAMPS libraries
#
#-------------------------------------------------------------------------
from gen.lib import (MediaObject, Person, Family, Source, Event, Place, 
                     Repository, Note, GenderStats, Researcher)
from gen.utils.callback import Callback

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
from gen.db.dbconst import (PERSON_KEY, FAMILY_KEY, SOURCE_KEY, EVENT_KEY, 
                            MEDIA_KEY, PLACE_KEY, REPOSITORY_KEY, NOTE_KEY, 
                            REFERENCE_KEY)

_UNDO_SIZE = 1000


# The following two dictionaries provide fast translation
# between the primary class names and the keys used to reference
# these classes in the database tables. Beware that changing
# these maps or modifying the values of the keys will break
# existing databases.

CLASS_TO_KEY_MAP = {Person.__name__: PERSON_KEY, 
                    Family.__name__: FAMILY_KEY, 
                    Source.__name__: SOURCE_KEY, 
                    Event.__name__: EVENT_KEY, 
                    MediaObject.__name__: MEDIA_KEY, 
                    Place.__name__: PLACE_KEY, 
                    Repository.__name__:REPOSITORY_KEY,
                    Note.__name__: NOTE_KEY}

KEY_TO_CLASS_MAP = {PERSON_KEY: Person.__name__, 
                    FAMILY_KEY: Family.__name__, 
                    SOURCE_KEY: Source.__name__, 
                    EVENT_KEY: Event.__name__, 
                    MEDIA_KEY: MediaObject.__name__, 
                    PLACE_KEY: Place.__name__, 
                    REPOSITORY_KEY: Repository.__name__,
                    NOTE_KEY: Note.__name__}

_SIGBASE = ('person', 'family', 'source', 'event', 
            'media', 'place', 'repository', 'reference', 'note')

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

class DbGrdb(Callback):
    """
    GRAMPS database object. This object is a base class for all
    database interfaces.
    """

    # This holds a reference to the gramps Config module if
    # it is available, it is setup by the factory methods.
    __config__ = None
    
    __signals__ = {
        'person-add'         : (list, ), 
        'person-update'      : (list, ), 
        'person-delete'      : (list, ), 
        'person-rebuild'     : None, 
        'family-add'         : (list, ), 
        'family-update'      : (list, ), 
        'family-delete'      : (list, ), 
        'family-rebuild'     : None, 
        'source-add'         : (list, ), 
        'source-update'      : (list, ), 
        'source-delete'      : (list, ), 
        'source-rebuild'     : None, 
        'place-add'          : (list, ), 
        'place-update'       : (list, ), 
        'place-delete'       : (list, ), 
        'place-rebuild'      : None, 
        'media-add'          : (list, ), 
        'media-update'       : (list, ), 
        'media-delete'       : (list, ), 
        'media-rebuild'      : None, 
        'event-add'          : (list, ), 
        'event-update'       : (list, ), 
        'event-delete'       : (list, ), 
        'event-rebuild'      : None, 
        'repository-add'     : (list, ), 
        'repository-update'  : (list, ), 
        'repository-delete'  : (list, ), 
        'repository-rebuild' : None, 
        'note-add'           : (list, ), 
        'note-update'        : (list, ), 
        'note-delete'        : (list, ), 
        'note-rebuild'       : None, 
        'long-op-start'      : (object, ),
        'long-op-heartbeat'  : None,
        'long-op-end'        : None,
        'home-person-changed': None,
        }
    
    # If this is True logging will be turned on.
    try:
        _LOG_ALL = int(os.environ.get('GRAMPS_SIGNAL', "0")) == 1
    except:
        _LOG_ALL = False


    def __init__(self):
        """
        Create a new DbBase instance. 
        
        A new GrampDbBase class should never be directly created. Only classes 
        derived from this class should be created.
        """

        Callback.__init__(self)

        self.set_person_id_prefix('I%04d')
        self.set_object_id_prefix('O%04d')
        self.set_family_id_prefix('F%04d')
        self.set_source_id_prefix('S%04d')
        self.set_place_id_prefix('P%04d')
        self.set_event_id_prefix('E%04d')
        self.set_repository_id_prefix('R%04d')
        self.set_note_id_prefix('N%04d')

        self.readonly = False
        self.rand = random.Random(time.time())
        self.smap_index = 0
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
        self.marker_names = set()
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
        self.oid_trans = {}
        self.rid_trans = {}
        self.nid_trans = {}
        self.eid_trans = {}
        self.env = None
        self.person_map = {}
        self.family_map = {}
        self.place_map  = {}
        self.source_map = {}
        self.repository_map  = {}
        self.note_map = {}
        self.media_map  = {}
        self.event_map  = {}
        self.metadata   = {}
        self.name_group = {}
        self.undo_callback = None
        self.redo_callback = None
        self.undo_history_callback = None
        self.modified   = 0

        self.undoindex  = -1
        self.translist  = [None] * _UNDO_SIZE
        self.abort_possible = True
        self.undo_history_timestamp = 0
        self.default = None
        self.owner = Researcher()
        self.name_formats = []
        self.bookmarks = DbBookmarks()
        self.family_bookmarks = DbBookmarks()
        self.event_bookmarks = DbBookmarks()
        self.place_bookmarks = DbBookmarks()
        self.source_bookmarks = DbBookmarks()
        self.repo_bookmarks = DbBookmarks()
        self.media_bookmarks = DbBookmarks()
        self.note_bookmarks = DbBookmarks()
        self._bm_changes = 0
        self.path = ""
        self.surname_list = []

    def set_prefixes(self, person, media, family, source, place, event,
                     repository, note):
        self.person_prefix = self._validated_id_prefix(person, 'I')
        self.mediaobject_prefix = self._validated_id_prefix(media, 'M')
        self.family_prefix = self._validated_id_prefix(family, 'F')
        self.source_prefix = self._validated_id_prefix(source, 'S')
        self.place_prefix = self._validated_id_prefix(place, 'P')
        self.event_prefix = self._validated_id_prefix(event, 'E')
        self.repository_prefix = self._validated_id_prefix(repository, 'R')
        self.note_prefix = self._validated_id_prefix(note, 'N')

    def rebuild_secondary(self, callback):
        pass

    def version_supported(self):
        """Return True when the file has a supported version."""
        return True

    def need_scema_upgrade(self):
        return False

    def gramps_upgrade(self):
        pass

    def del_person(self, handle):
        pass

    def del_source(self, handle):
        pass

    def del_repository(self, handle):
        pass

    def del_note(self, handle):
        pass

    def del_place(self, handle):
        pass

    def del_media(self, handle):
        pass

    def del_family(self, handle):
        pass

    def del_event(self, handle):
        pass

    def create_id(self):
        return "%08x%08x" % ( int(time.time()*10000), 
                              self.rand.randint(0, maxint))

    def get_person_cursor(self):
        raise NotImplementedError

    def get_family_cursor(self):
        raise NotImplementedError

    def get_event_cursor(self):
        raise NotImplementedError

    def get_place_cursor(self):
        raise NotImplementedError

    def get_source_cursor(self):
        raise NotImplementedError

    def get_media_cursor(self):
        raise NotImplementedError

    def get_repository_cursor(self):
        raise NotImplementedError

    def get_note_cursor(self):
        raise NotImplementedError

    def open_undodb(self):
        if not self.readonly:
            self.undolog = "%s.undo" % self.full_name
            self.undodb = db.DB()
            self.undodb.open(self.undolog, db.DB_RECNO, db.DB_CREATE)

    def close_undodb(self):
        if not self.readonly:
            self.undodb.close()
            try:
                os.remove(self.undolog)
            except:
                pass

    def load(self, name, callback, mode="w"):
        """
        Open the specified database. 
        
        The method needs to be overridden in the derived class.
        """
        raise NotImplementedError

    def close(self):
        """
        Close the specified database. 
        
        The method needs to be overridden in the derived class.
        """
        pass
        
    def is_open(self):
        """
        Return 1 if the database has been opened.
        """
        return self.db_is_open

    def request_rebuild(self):
        """
        Notify clients that the data has changed significantly, and that all
        internal data dependent on the database should be rebuilt.
        Note that all rebuild signals on all objects are emitted at the same
        time. It is correct to assume that this is always the case.
        TODO: it might be better to replace these rebuild signals by one single
                database-rebuild signal.
        """
        self.emit('person-rebuild')
        self.emit('family-rebuild')
        self.emit('place-rebuild')
        self.emit('source-rebuild')
        self.emit('media-rebuild')
        self.emit('event-rebuild')
        self.emit('repository-rebuild')
        self.emit('note-rebuild')
            
    def commit_base(self, obj, data_map, key, update_list, add_list, 
                     transaction, change_time):
        """
        Commit the specified Person to the database, storing the changes as 
        part of the transaction.
        """
        if self.readonly or not obj or not obj.handle:
            return 

        if change_time:
            obj.change = int(change_time)
        else:
            obj.change = int(time.time())
        handle = str(obj.handle)
        
        self.update_reference_map(obj, transaction)

        if transaction.batch:
            data_map[handle] = obj.serialize()
            old_data = None
        else:
            old_data = data_map.get(handle)
            new_data = obj.serialize()
            transaction.add(key, handle, old_data, new_data)
            if old_data:
                update_list.append((handle, new_data))
            else:
                add_list.append((handle, new_data))
        return old_data

    def commit_person(self, person, transaction, change_time=None):
        """
        Commit the specified Person to the database, storing the changes as 
        part of the transaction.
        """

        old_data = self.commit_base(
            person, self.person_map, PERSON_KEY, transaction.person_update, 
            transaction.person_add, transaction, change_time)
        if old_data:
            old_person = Person(old_data)
            if (old_data[2] != person.gender or
                old_data[3][4]!= person.primary_name.first_name):
                self.genderStats.uncount_person(old_person)
                self.genderStats.count_person(person)
            if (old_data[3][5]!=person.primary_name.surname):
                self.remove_from_surname_list(old_person)
                self.add_to_surname_list(person, transaction.batch)
        else:
            self.genderStats.count_person(person)
            self.add_to_surname_list(person, transaction.batch)

        self.individual_attributes.update(
            [str(attr.type) for attr in person.attribute_list
             if attr.type.is_custom() and str(attr.type)])

        if person.marker.is_custom():
            self.marker_names.add(str(person.marker))

        self.event_role_names.update([str(eref.role)
                                      for eref in person.event_ref_list
                                      if eref.role.is_custom()])

        self.name_types.update([str(name.type)
                                for name in ([person.primary_name]
                                             + person.alternate_names)
                                if name.type.is_custom()])
        
        self.url_types.update([str(url.type) for url in person.urls
                               if url.type.is_custom()])

        attr_list = []
        for mref in person.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_media_object(self, obj, transaction, change_time=None):
        """
        Commit the specified MediaObject to the database, storing the changes
        as part of the transaction.
        """
        
        self.commit_base(obj, self.media_map, MEDIA_KEY, 
                          transaction.media_update, transaction.media_add, 
                          transaction, change_time)
        self.media_attributes.update(
            [str(attr.type) for attr in obj.attribute_list
             if attr.type.is_custom() and str(attr.type)])
            
    def commit_source(self, source, transaction, change_time=None):
        """
        Commit the specified Source to the database, storing the changes as 
        part of the transaction.
        """

        self.commit_base(source, self.source_map, SOURCE_KEY, 
                          transaction.source_update, transaction.source_add, 
                          transaction, change_time)

        self.source_media_types.update(
            [str(ref.media_type) for ref in source.reporef_list
             if ref.media_type.is_custom()])       

        attr_list = []
        for mref in source.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_place(self, place, transaction, change_time=None):
        """
        Commit the specified Place to the database, storing the changes as 
        part of the transaction.
        """

        self.commit_base(place, self.place_map, PLACE_KEY, 
                          transaction.place_update, transaction.place_add, 
                          transaction, change_time)

        self.url_types.update([str(url.type) for url in place.urls
                               if url.type.is_custom()])

        attr_list = []
        for mref in place.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_personal_event(self, event, transaction, change_time=None):
        if event.type.is_custom():
            self.individual_event_names.add(str(event.type))
        self.commit_event(event, transaction, change_time)

    def commit_family_event(self, event, transaction, change_time=None):
        if event.type.is_custom():
            self.family_event_names.add(str(event.type))
        self.commit_event(event, transaction, change_time)

    def commit_event(self, event, transaction, change_time=None):
        """
        Commit the specified Event to the database, storing the changes as 
        part of the transaction.
        """
        self.commit_base(event, self.event_map, EVENT_KEY, 
                          transaction.event_update, transaction.event_add, 
                          transaction, change_time)

        attr_list = []
        for mref in event.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_family(self, family, transaction, change_time=None):
        """
        Commit the specified Family to the database, storing the changes as 
        part of the transaction.
        """

        self.commit_base(family, self.family_map, FAMILY_KEY, 
                          transaction.family_update, transaction.family_add, 
                          transaction, change_time)

        self.family_attributes.update(
            [str(attr.type) for attr in family.attribute_list
             if attr.type.is_custom() and str(attr.type)])

        rel_list = []
        for ref in family.child_ref_list:
            if ref.frel.is_custom():
                rel_list.append(str(ref.frel))
            if ref.mrel.is_custom():
                rel_list.append(str(ref.mrel))
        self.child_ref_types.update(rel_list)

        self.event_role_names.update(
            [str(eref.role) for eref in family.event_ref_list
             if eref.role.is_custom()])

        if family.type.is_custom():
            self.family_rel_types.add(str(family.type))

        attr_list = []
        for mref in family.media_list:
            attr_list += [str(attr.type) for attr in mref.attribute_list
                          if attr.type.is_custom() and str(attr.type)]
        self.media_attributes.update(attr_list)

    def commit_repository(self, repository, transaction, change_time=None):
        """
        Commit the specified Repository to the database, storing the changes
        as part of the transaction.
        """
        self.commit_base(repository, self.repository_map, REPOSITORY_KEY, 
                          transaction.repository_update,
                          transaction.repository_add, 
                          transaction, change_time)

        if repository.type.is_custom():
            self.repository_types.add(str(repository.type))

        self.url_types.update([str(url.type) for url in repository.urls
                               if url.type.is_custom()])

    def commit_note(self, note, transaction, change_time=None):
        """
        Commit the specified Note to the database, storing the changes as part 
        of the transaction.
        """
        self.commit_base(note, self.note_map, NOTE_KEY, 
                          transaction.note_update,
                          transaction.note_add, 
                          transaction, change_time)

        if note.type.is_custom():
            self.note_types.add(str(note.type))

    def find_next_person_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Person object based off the 
        person ID prefix.
        """
        index = self.person_prefix % self.pmap_index
        while self.id_trans.has_key(str(index)):
            self.pmap_index += 1
            index = self.person_prefix % self.pmap_index
        self.pmap_index += 1
        return index

    def find_next_place_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Place object based off the 
        place ID prefix.
        """
        index = self.place_prefix % self.lmap_index
        while self.pid_trans.has_key(str(index)):
            self.lmap_index += 1
            index = self.place_prefix % self.lmap_index
        self.lmap_index += 1
        return index

    def find_next_event_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Event object based off the 
        event ID prefix.
        """
        index = self.event_prefix % self.emap_index
        while self.eid_trans.has_key(str(index)):
            self.emap_index += 1
            index = self.event_prefix % self.emap_index
        self.emap_index += 1
        return index

    def find_next_object_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a MediaObject object based
        off the media object ID prefix.
        """
        index = self.mediaobject_prefix % self.omap_index
        while self.oid_trans.has_key(str(index)):
            self.omap_index += 1
            index = self.mediaobject_prefix % self.omap_index
        self.omap_index += 1
        return index

    def find_next_source_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Source object based off the 
        source ID prefix.
        """
        index = self.source_prefix % self.smap_index
        while self.sid_trans.has_key(str(index)):
            self.smap_index += 1
            index = self.source_prefix % self.smap_index
        self.smap_index += 1
        return index

    def find_next_family_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Family object based off the 
        family ID prefix.
        """
        index = self.family_prefix % self.fmap_index
        while self.fid_trans.has_key(str(index)):
            self.fmap_index += 1
            index = self.family_prefix % self.fmap_index
        self.fmap_index += 1
        return index

    def find_next_repository_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Respository object based 
        off the repository ID prefix.
        """
        index = self.repository_prefix % self.rmap_index
        while self.rid_trans.has_key(str(index)):
            self.rmap_index += 1
            index = self.repository_prefix % self.rmap_index
        self.rmap_index += 1
        return index

    def find_next_note_gramps_id(self):
        """
        Return the next available GRAMPS' ID for a Note object based off the 
        note ID prefix.
        """
        index = self.note_prefix % self.nmap_index
        while self.nid_trans.has_key(str(index)):
            self.nmap_index += 1
            index = self.note_prefix % self.nmap_index
        self.nmap_index += 1
        return index

    def get_from_handle(self, handle, class_type, data_map):
        data = data_map.get(str(handle))
        if data:
            newobj = class_type()
            newobj.unserialize(data)
            return newobj
        return None

    def get_person_from_handle(self, handle):
        """
        Find a Person in the database from the passed gramps' ID.
        
        If no such Person exists, None is returned.
        """
        return self.get_from_handle(handle, Person, self.person_map)

    def get_source_from_handle(self, handle):
        """
        Find a Source in the database from the passed gramps' ID.
        
        If no such Source exists, None is returned.
        """
        return self.get_from_handle(handle, Source, self.source_map)

    def get_object_from_handle(self, handle):
        """
        Find an Object in the database from the passed gramps' ID.
        
        If no such Object exists, None is returned.
        """
        return self.get_from_handle(handle, MediaObject, self.media_map)

    def get_place_from_handle(self, handle):
        """
        Find a Place in the database from the passed gramps' ID.
        
        If no such Place exists, None is returned.
        """
        return self.get_from_handle(handle, Place, self.place_map)

    def get_event_from_handle(self, handle):
        """
        Find a Event in the database from the passed gramps' ID.
        
        If no such Event exists, None is returned.
        """
        return self.get_from_handle(handle, Event, self.event_map)

    def get_family_from_handle(self, handle):
        """
        Find a Family in the database from the passed gramps' ID.
        
        If no such Family exists, None is returned.
        """
        return self.get_from_handle(handle, Family, self.family_map)

    def get_repository_from_handle(self, handle):
        """
        Find a Repository in the database from the passed gramps' ID.
        
        If no such Repository exists, None is returned.
        """
        return self.get_from_handle(handle, Repository, self.repository_map)

    def get_note_from_handle(self, handle):
        """
        Find a Note in the database from the passed gramps' ID.
        
        If no such Note exists, None is returned.
        """
        return self.get_from_handle(handle, Note, self.note_map)

    def find_from_handle(self, handle, transaction, class_type, dmap,
                          add_func):
        """
        Find a object of class_type in the database from the passed handle.
        
        If no object exists, a new object is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        obj = class_type()
        handle = str(handle)
        new = True
        if handle in dmap:
            obj.unserialize(dmap.get(handle))
            #references create object with id None before object is really made
            if obj.gramps_id is not None:
                new = False
        else:
            obj.set_handle(handle)
            add_func(obj, transaction)
        return obj, new

    def __check_from_handle(self, handle, transaction, class_type, dmap,
                            add_func, set_gid=True):
        handle = str(handle)
        if handle not in dmap:
            obj = class_type()
            obj.set_handle(handle)
            add_func(obj, transaction, set_gid=set_gid)

    def find_person_from_handle(self, handle, transaction):
        """
        Find a Person in the database from the passed handle.
        
        If no such Person exists, a new Person is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Person, 
                                     self.person_map, self.add_person)

    def find_source_from_handle(self, handle, transaction):
        """
        Find a Source in the database from the passed handle.
        
        If no such Source exists, a new Source is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Source, 
                                     self.source_map, self.add_source)

    def find_event_from_handle(self, handle, transaction):
        """
        Find a Event in the database from the passed handle.
        
        If no such Event exists, a new Event is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Event, 
                                     self.event_map, self.add_event)

    def find_object_from_handle(self, handle, transaction):
        """
        Find a MediaObject in the database from the passed handle.
        
        If no such MediaObject exists, a new Object is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, MediaObject, 
                                     self.media_map, self.add_object)

    def find_place_from_handle(self, handle, transaction):
        """
        Find a Place in the database from the passed handle.
        
        If no such Place exists, a new Place is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Place, 
                                     self.place_map, self.add_place)

    def find_family_from_handle(self, handle, transaction):
        """
        Find a Family in the database from the passed handle.
        
        If no such Family exists, a new Family is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Family, 
                                     self.family_map, self.add_family)

    def find_repository_from_handle(self, handle, transaction):
        """
        Find a Repository in the database from the passed handle.
        
        If no such Repository exists, a new Repository is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Repository, 
                                     self.repository_map, self.add_repository)

    def find_note_from_handle(self, handle, transaction):
        """
        Find a Note in the database from the passed handle.
        
        If no such Note exists, a new Note is added to the database.
        
        @return: Returns a tuple, first the object, second a bool which is True
                 if the object is new
        @rtype: tuple
        """
        return self.find_from_handle(handle, transaction, Note, 
                                     self.note_map, self.add_note)

    def check_person_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a Person with the passed handle exists in the database.
        
        If no such Person exists, a new Person is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Person, 
                                 self.person_map, self.add_person, 
                                 set_gid = set_gid)

    def check_source_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a Source with the passed handle exists in the database.
        
        If no such Source exists, a new Source is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Source, 
                                 self.source_map, self.add_source, 
                                 set_gid=set_gid)
                                
    def check_event_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether an Event with the passed handle exists in the database.
        
        If no such Event exists, a new Event is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Event, 
                                 self.event_map, self.add_event, 
                                 set_gid=set_gid)

    def check_object_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a MediaObject with the passed handle exists in the 
        database. 
        
        If no such MediaObject exists, a new Object is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """

        self.__check_from_handle(handle, transaction, MediaObject, 
                                 self.media_map, self.add_object, 
                                 set_gid=set_gid)

    def check_place_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a Place with the passed handle exists in the database.
        
        If no such Place exists, a new Place is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Place, 
                                 self.place_map, self.add_place, 
                                 set_gid=set_gid)

    def check_family_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a Family with the passed handle exists in the database.
        
        If no such Family exists, a new Family is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Family, 
                                 self.family_map, self.add_family, 
                                 set_gid=set_gid)

    def check_repository_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a Repository with the passed handle exists in the
        database. 
        
        If no such Repository exists, a new Repository is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Repository, 
                                 self.repository_map, self.add_repository, 
                                 set_gid=set_gid)

    def check_note_from_handle(self, handle, transaction, set_gid=True):
        """
        Check whether a Note with the passed handle exists in the database. 
        
        If no such Note exists, a new Note is added to the database.
        If set_gid then a new gramps_id is created, if not, None is used.
        """
        self.__check_from_handle(handle, transaction, Note, 
                                 self.note_map, self.add_note, 
                                 set_gid=set_gid)

    def get_person_from_gramps_id(self, val):
        """
        Find a Person in the database from the passed GRAMPS ID.
        
        If no such Person exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_family_from_gramps_id(self, val):
        """
        Find a Family in the database from the passed GRAMPS ID.
        
        If no such Family exists, None is returned.
        Need to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_event_from_gramps_id(self, val):
        """
        Find an Event in the database from the passed GRAMPS ID.
        
        If no such Event exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_place_from_gramps_id(self, val):
        """
        Find a Place in the database from the passed gramps' ID.
        
        If no such Place exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_source_from_gramps_id(self, val):
        """
        Find a Source in the database from the passed gramps' ID.
        
        If no such Source exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_object_from_gramps_id(self, val):
        """
        Find a MediaObject in the database from the passed gramps' ID.

        If no such MediaObject exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_repository_from_gramps_id(self, val):
        """
        Find a Repository in the database from the passed gramps' ID.

        If no such Repository exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_note_from_gramps_id(self, val):
        """
        Find a Note in the database from the passed gramps' ID.

        If no such Note exists, None is returned.
        Needs to be overridden by the derived classderri.
        """
        raise NotImplementedError

    def __add_object(self, obj, transaction, find_next_func, commit_func):
        if find_next_func and not obj.gramps_id:
            obj.gramps_id = find_next_func()
        if not obj.handle:
            obj.handle = self.create_id()
        commit_func(obj, transaction)
        if obj.__class__.__name__ == 'Person':
            self.genderStats.count_person (obj)
        return obj.handle

    def add_person(self, person, transaction, set_gid=True):
        """
        Add a Person to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(person, transaction, 
                                    self.find_next_person_gramps_id, 
                                    self.commit_person)
        else:
            return self.__add_object(person, transaction, 
                                    None, 
                                    self.commit_person)

    def add_family(self, family, transaction, set_gid=True):
        """
        Add a Family to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(family, transaction, 
                                    self.find_next_family_gramps_id, 
                                    self.commit_family)
        else:
            return self.__add_object(family, transaction, 
                                    None, 
                                    self.commit_family)

    def add_source(self, source, transaction, set_gid=True):
        """
        Add a Source to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(source, transaction, 
                                    self.find_next_source_gramps_id, 
                                    self.commit_source)
        else :
            return self.__add_object(source, transaction, 
                                None, 
                                self.commit_source)

    def add_event(self, event, transaction, set_gid=True):
        """
        Add an Event to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(event, transaction, 
                                    self.find_next_event_gramps_id, 
                                    self.commit_event)
        else:
            return self.__add_object(event, transaction, 
                                    None, 
                                    self.commit_event)

    def add_person_event(self, event, transaction):
        """
        Add an Event to the database, assigning internal IDs if they have
        not already been defined.
        """
        if event.type.is_custom():
            self.individual_event_names.add(str(event.type))
        return self.add_event(event, transaction)

    def add_family_event(self, event, transaction):
        """
        Add an Event to the database, assigning internal IDs if they have
        not already been defined.
        """
        if event.type.is_custom():
            self.family_event_names.add(str(event.type))
        return self.add_event(event, transaction)

    def add_place(self, place, transaction, set_gid=True):
        """
        Add a Place to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(place, transaction, 
                                    self.find_next_place_gramps_id, 
                                    self.commit_place)
        else:
            return self.__add_object(place, transaction, 
                                    None,
                                    self.commit_place)

    def add_object(self, obj, transaction, set_gid=True):
        """
        Add a MediaObject to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(obj, transaction, 
                                    self.find_next_object_gramps_id, 
                                    self.commit_media_object)
        else:
            return self.__add_object(obj, transaction, 
                                    None, 
                                    self.commit_media_object)

    def add_repository(self, obj, transaction, set_gid=True):
        """
        Add a Repository to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(obj, transaction, 
                                    self.find_next_repository_gramps_id, 
                                    self.commit_repository)
        else:
            return self.__add_object(obj, transaction, 
                                    None,
                                    self.commit_repository)

    def add_note(self, obj, transaction, set_gid=True):
        """
        Add a Note to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then gramps_id is not set.
        """
        if set_gid:
            return self.__add_object(obj, transaction, 
                                     self.find_next_note_gramps_id, 
                                     self.commit_note)
        else:
            return self.__add_object(obj, transaction, 
                                     None, 
                                     self.commit_note)

    def get_name_group_mapping(self, name):
        """
        Return the default grouping name for a surname.
        """
        return unicode(self.name_group.get(str(name), name))

    def get_name_group_keys(self):
        """
        Return the defined names that have been assigned to a default grouping.
        """
        return map(unicode, self.name_group.keys())

    def has_name_group_key(self, name):
        """
        Return if a key exists in the name_group table.
        """
        return self.name_group.has_key(str(name))

    def set_name_group_mapping(self, name, group):
        """
        Set the default grouping name for a surname. 
        
        Needs to be overridden in the derived class.
        """
        raise NotImplementedError
        
    @staticmethod
    def get_number_of_records(table):
        return table.stat(db.DB_FAST_STAT)['nkeys'] 

    def get_number_of_people(self):
        """
        Return the number of people currently in the database.
        """
        if self.db_is_open:
            return self.get_number_of_records(self.person_map)
            #return len(self.person_map)
        else:
            return 0

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

    def get_number_of_media_objects(self):
        """
        Return the number of media objects currently in the database.
        """
        return len(self.media_map)

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

    def all_handles(self, table):
        return table.keys()
        
    def get_person_handles(self, sort_handles=True):
        """
        Return a list of database handles, one handle for each Person in
        the database. 
        
        If sort_handles is True, the list is sorted by surnames.
        """
        if self.db_is_open:
            if sort_handles:
                with self.get_person_cursor() as cursor:
                    slist = sorted((data[3][3], key) for key, data in cursor)
                return [x[1] for x in slist]
            else:
                return self.all_handles(self.person_map)
        return []

    def iter_person_handles(self):
        """
        Return an iterator over handles for Persons in the database
        """
        with self.get_person_cursor() as cursor:
            for key, data in cursor:
                yield key

    def get_place_handles(self, sort_handles=True):
        """
        Return a list of database handles, one handle for each Place in
        the database. 
        
        If sort_handles is True, the list is sorted by Place title.
        """
        if self.db_is_open:
            if sort_handles:
                with self.get_place_cursor() as cursor:
                    slist = sorted((data[2], key) for key, data in cursor)
                return [x[1] for x in slist]
            else:
                return self.all_handles(self.place_map)
        return []
        
    def iter_place_handles(self):
        """
        Return an iterator over handles for Places in the database
        """
        with self.get_place_cursor() as cursor:
            for key, data in cursor:
                yield key
                
    def get_source_handles(self, sort_handles=True):
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
        
    def iter_source_handles(self):
        """
        Return an iterator over handles for Sources in the database
        """
        with self.get_source_cursor() as cursor:
            for key, data in cursor:
                yield key
                
    def get_media_object_handles(self, sort_handles=True):
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
        
    def iter_media_object_handles(self):
        """
        Return an iterator over handles for Media in the database
        """
        with self.get_media_cursor() as cursor:
            for key, data in cursor:
                yield key

    def get_event_handles(self):
        """
        Return a list of database handles, one handle for each Event in the 
        database. 
        """
        if self.db_is_open:
            return self.all_handles(self.event_map)
        return []
        
    def iter_event_handles(self):
        """
        Return an iterator over handles for Events in the database
        """
        with self.get_event_cursor() as cursor:
            for key, data in cursor:
                yield key

    def get_family_handles(self):
        """
        Return a list of database handles, one handle for each Family in
        the database.
        """
        if self.db_is_open:
            return self.all_handles(self.family_map)
        return []
        
    def iter_family_handles(self):
        """
        Return an iterator over handles for Families in the database
        """
        with self.get_family_cursor() as cursor:
            for key, data in cursor:
                yield key        

    def get_repository_handles(self):
        """
        Return a list of database handles, one handle for each Repository in
        the database.
        """
        if self.db_is_open:
            return self.all_handles(self.repository_map)
        return []
        
    def iter_repository_handles(self):
        """
        Return an iterator over handles for Repositories in the database
        """
        with self.get_repository_cursor() as cursor:
            for key, data in cursor:
                yield key 

    def get_note_handles(self):
        """
        Return a list of database handles, one handle for each Note in the 
        database.
        """
        if self.db_is_open:
            return self.all_handles(self.note_map)
        return []
        
    def iter_note_handles(self):
        """
        Return an iterator over handles for Notes in the database
        """
        with self.get_note_cursor() as cursor:
            for key, data in cursor:
                yield key

    def get_gramps_ids(self, obj_key):
        key2table = {
            PERSON_KEY:     self.id_trans, 
            FAMILY_KEY:     self.fid_trans, 
            SOURCE_KEY:     self.sid_trans, 
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
            EVENT_KEY:      self.eid_trans, 
            MEDIA_KEY:      self.oid_trans, 
            PLACE_KEY:      self.pid_trans, 
            REPOSITORY_KEY: self.rid_trans, 
            NOTE_KEY:       self.nid_trans, 
            }

        table = key2table[obj_key]
        #return str(gramps_id) in table
        return table.has_key(str(gramps_id))

    def find_initial_person(self):
        person = self.get_default_person()
        if not person:
            the_ids = self.get_gramps_ids(PERSON_KEY)
            if the_ids:
                person = self.get_person_from_gramps_id(min(the_ids))
        return person

    def _validated_id_prefix(self, val, default):
        if isinstance(val, basestring) and val:
            try:
                str_ = val % 1
            except TypeError:           # missing conversion specifier
                prefix_var = val + "%d"
            else:
                prefix_var = val        # OK as given
        else:
            prefix_var = default+"%04d" # not a string or empty string
        return prefix_var
    
    def set_person_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Person ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as I%d or I%04d.
        """
        self.person_prefix = self._validated_id_prefix(val, "I")
            
    def set_source_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Source ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as S%d or S%04d.
        """
        self.source_prefix = self._validated_id_prefix(val, "S")
            
    def set_object_id_prefix(self, val):
        """
        Set the naming template for GRAMPS MediaObject ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as O%d or O%04d.
        """
        self.mediaobject_prefix = self._validated_id_prefix(val, "O")

    def set_place_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Place ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as P%d or P%04d.
        """
        self.place_prefix = self._validated_id_prefix(val, "P")

    def set_family_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Family ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as F%d
        or F%04d.
        """
        self.family_prefix = self._validated_id_prefix(val, "F")

    def set_event_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Event ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as E%d or E%04d.
        """
        self.event_prefix = self._validated_id_prefix(val, "E")

    def set_repository_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Repository ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as R%d or R%04d.
        """
        self.repository_prefix = self._validated_id_prefix(val, "R")

    def set_note_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Note ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as N%d or N%04d.
        """
        self.note_prefix = self._validated_id_prefix(val, "N")

    def transaction_begin(self, msg="", batch=False, no_magic=False):
        """
        Create a new Transaction tied to the current UNDO database. 
        
        The transaction has no effect until it is committed using the
        transaction_commit function of the this database object.
        """
        if self._LOG_ALL:
            LOG.debug("%s: Transaction begin '%s'\n"
                      % (self.__class__.__name__, str(msg)))
        if batch:
            # A batch transaction does not store the commits
            # Aborting the session completely will become impossible.
            self.abort_possible = False
            self.undo_history_timestamp = time.time()
            # Undo is also impossible after batch transaction
            self.undoindex = -1
            self.translist  = [None] * _UNDO_SIZE
        return Transaction(msg, self.undodb, batch)

    def transaction_commit(self, transaction, msg):
        """
        Commit the transaction to the associated UNDO database.
        """
        if self._LOG_ALL:
            LOG.debug("%s: Transaction commit '%s'\n"
                      % (self.__class__.__name__, str(msg)))

        if not len(transaction) or self.readonly:
            return

        transaction.set_description(msg)
        transaction.timestamp = time.time()
        self.undoindex += 1                    
        if self.undoindex >= _UNDO_SIZE:
            # We overran the undo size.
            # Aborting the session completely will become impossible.
            self.abort_possible = False
            self.undo_history_timestamp = time.time()            
            self.translist = self.translist[0:-1] + [ transaction ]
        else:
            self.translist[self.undoindex] = transaction
            # Real commit erases all subsequent transactions
            # to there's no Redo anymore.
            for index in range(self.undoindex+1, _UNDO_SIZE):
                self.translist[index] = None

        person_add = self.do_commit(transaction.person_add, self.person_map)
        family_add = self.do_commit(transaction.family_add, self.family_map)
        source_add = self.do_commit(transaction.source_add, self.source_map)
        place_add = self.do_commit(transaction.place_add, self.place_map)
        media_add = self.do_commit(transaction.media_add, self.media_map)
        event_add = self.do_commit(transaction.event_add, self.event_map)
        repository_add = self.do_commit(transaction.repository_add, 
                                        self.repository_map)

        note_add = self.do_commit(transaction.note_add, self.note_map)
        person_upd = self.do_commit(transaction.person_update, self.person_map)
        family_upd = self.do_commit(transaction.family_update, self.family_map)
        source_upd = self.do_commit(transaction.source_update, self.source_map)
        place_upd = self.do_commit(transaction.place_update, self.place_map)
        media_upd = self.do_commit(transaction.media_update, self.media_map)
        event_upd = self.do_commit(transaction.event_update, self.event_map)
        repository_upd = self.do_commit(transaction.repository_update, 
                                        self.repository_map)
        note_upd = self.do_commit(transaction.note_update, self.note_map)

        self.__do_emit('person', person_add, person_upd, transaction.person_del)
        self.__do_emit('family', family_add, family_upd, transaction.family_del)
        self.__do_emit('event',  event_add,  event_upd,  transaction.event_del)
        self.__do_emit('source', source_add, source_upd, transaction.source_del)
        self.__do_emit('place',  place_add,  place_upd,  transaction.place_del)
        self.__do_emit('media',  media_add,  media_upd,  transaction.media_del)
        self.__do_emit('repository', repository_add, repository_upd, 
                      transaction.repository_del)
        self.__do_emit('note',   note_add,   note_upd,   transaction.note_del)

        self.__do_del(transaction.person_del,     self.del_person)
        self.__do_del(transaction.family_del,     self.del_family)
        self.__do_del(transaction.place_del,      self.del_place)
        self.__do_del(transaction.source_del,     self.del_source)
        self.__do_del(transaction.event_del,      self.del_event)
        self.__do_del(transaction.media_del,      self.del_media)
        self.__do_del(transaction.repository_del, self.del_repository)
        self.__do_del(transaction.note_del,       self.del_note)

        if self.undo_callback:
            self.undo_callback(_("_Undo %s") % transaction.get_description())
        if self.redo_callback:
            self.redo_callback(None)
        if self.undo_history_callback:
            self.undo_history_callback()

    def __do_emit(self, objtype, add_list, upd_list, del_list):
        if add_list:
            self.emit(objtype + '-add', (add_list, ))
        if upd_list:
            self.emit(objtype + '-update', (upd_list, ))
        if del_list:
            self.emit(objtype + '-delete', (del_list, ))

    def __do_del(self, del_list, func):
        map(func, del_list)
        return del_list

    def do_commit(self, add_list, db_map):
        retlist = []
        for (handle, data) in add_list:
            db_map[handle] = data
            retlist.append(str(handle))
        return retlist

    def undo_available(self):
        """
        Return boolean of whether or not there's a possibility of undo.
        """
        if self.undoindex == -1 or self.readonly:
            return False
        return True
        
    def redo_available(self):
        """
        Return boolean of whether or not there's a possibility of redo.
        """
        if self.undoindex >= _UNDO_SIZE or self.readonly:
            return False

        if self.translist[self.undoindex+1] is None:
            return False

        return True
        
    def undo(self, update_history=True):
        """
        Access the last committed transaction, and revert the data to the 
        state before the transaction was committed.
        """
        if not self.undo_available():
            return False

        transaction = self.translist[self.undoindex]

        mapbase = (self.person_map, self.family_map, self.source_map, 
                   self.event_map, self.media_map, self.place_map,
                   self.repository_map, {}, self.note_map)

        self.undoindex -= 1
        subitems = transaction.get_recnos()
        subitems.reverse()
        for record_id in subitems:
            (key, handle, old_data, new_data) = transaction.get_record(record_id)
            if key == REFERENCE_KEY:
                self.undo_reference(old_data, handle)
            else:
                self.undo_data(old_data, handle, mapbase[key], _SIGBASE[key])

        if self.undo_callback:
            if self.undo_available():
                new_transaction = self.translist[self.undoindex]
                self.undo_callback(_("_Undo %s")
                                   % new_transaction.get_description())
            else:
                self.undo_callback(None)

        if self.redo_callback:
            if self. redo_available():
                self.redo_callback(_("_Redo %s")
                                   % transaction.get_description())
            else:
                self.redo_callback(None)

        if update_history and self.undo_history_callback:
            self.undo_history_callback()
        return True

    def redo(self, update_history=True):
        """
        Accesse the last undone transaction, and revert the data to the state 
        before the transaction was undone.
        """

        if not self.redo_available():
            return False

        self.undoindex += 1
        transaction = self.translist[self.undoindex]
        mapbase = (self.person_map, self.family_map, self.source_map, 
                   self.event_map, self.media_map, self.place_map,
                   self.repository_map, {}, self.note_map)

        subitems = transaction.get_recnos()
        for record_id in subitems:
            (key, handle, old_data, new_data) = transaction.get_record(record_id)
            if key == REFERENCE_KEY:
                self.undo_reference(new_data, handle)
            else:
                self.undo_data(new_data, handle, mapbase[key], _SIGBASE[key])

        if self.undo_callback:
            if self.undo_available():
                self.undo_callback(_("_Undo %s")
                                   % transaction.get_description())
            else:
                self.undo_callback(None)

        if self.redo_callback:
            if self.redo_available():
                new_transaction = self.translist[self.undoindex+1]
                self.redo_callback(_("_Redo %s")
                                   % new_transaction.get_description())
            else:
                self.redo_callback(None)

        if update_history and self.undo_history_callback:
            self.undo_history_callback()
        return True

    def undo_reference(self, data, handle):
        pass

    def undo_data(self, data, handle, db_map, signal_root):
        if data is None:
            self.emit(signal_root + '-delete', ([handle], ))
            del db_map[handle]
        else:
            if handle in db_map:
                signal = signal_root + '-update'
            else:
                signal = signal_root + '-add'
            db_map[handle] = data
            self.emit(signal, ([handle], ))
    
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

    def build_surname_list(self):
        """
        Build the list of locale-sorted surnames contained in the database.
        
        The function must be overridden in the derived class.
        """
        raise NotImplementedError

    def sort_surname_list(self):
        self.surname_list.sort(key=locale.strxfrm)

    def add_to_surname_list(self, person, batch_transaction):
        if batch_transaction:
            return
        name = unicode(person.get_primary_name().get_surname())
        if name not in self.surname_list:
            self.surname_list.append(name)
            self.sort_surname_list()

    def remove_from_surname_list(self, person):
        """
        Check whether there are persons with the same surname left in
        the database. 
        
        If not then we need to remove the name from the list.
        The function must be overridden in the derived class.
        """
        raise NotImplementedError

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

    def set_default_person_handle(self, handle):
        """Set the default Person to the passed instance."""
        if (self.metadata is not None) and (not self.readonly):
            self.metadata['default'] = str(handle)
            self.emit('home-person-changed')

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
        Return a list of all Event types associated with Person instances in 
        the database.
        """
        return list(self.individual_event_names)

    def get_person_attribute_types(self):
        """
        Return a list of all Attribute types associated with Person instances 
        in the database.
        """
        return list(self.individual_attributes)

    def get_family_attribute_types(self):
        """
        Return a list of all Attribute types associated with Family instances 
        in the database.
        """
        return list(self.family_attributes)

    def get_family_event_types(self):
        """
        Return a list of all Event types associated with Family instances in 
        the database.
        """
        return list(self.family_event_names)

    def get_marker_types(self):
        """
        Return a list of all marker types available in the database.
        """
        return list(self.marker_names)
        
    def get_media_attribute_types(self):
        """
        Return a list of all Attribute types associated with Media and MediaRef 
        instances in the database.
        """
        return list(self.media_attributes)

    def get_family_relation_types(self):
        """
        Return a list of all relationship types associated with Family
        instances in the database.
        """
        return list(self.family_rel_types)

    def get_child_reference_types(self):
        """
        Return a list of all child reference types associated with Family
        instances in the database.
        """
        return list(self.child_ref_types)

    def get_event_roles(self):
        """
        Return a list of all custom event role names associated with Event
        instances in the database.
        """
        return list(self.event_role_names)

    def get_name_types(self):
        """
        Return a list of all custom names types associated with Person
        instances in the database.
        """
        return list(self.name_types)

    def get_repository_types(self):
        """
        Return a list of all custom repository types associated with Repository 
        instances in the database.
        """
        return list(self.repository_types)

    def get_note_types(self):
        """
        Return a list of all custom note types associated with Note instances 
        in the database.
        """
        return list(self.note_types)

    def get_source_media_types(self):
        """
        Return a list of all custom source media types associated with Source 
        instances in the database.
        """
        return list(self.source_media_types)

    def get_url_types(self):
        """
        Return a list of all custom names types associated with Url instances 
        in the database.
        """
        return list(self.url_types)

    def remove_person(self, handle, transaction):
        """
        Remove the Person specified by the database handle from the database, 
        preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """

        if self.readonly or not handle:
            return
        self.delete_primary_from_reference_map(handle, transaction)
        person = self.get_person_from_handle(handle)
        self.genderStats.uncount_person (person)
        self.remove_from_surname_list(person)
        if transaction.batch:
            self.del_person(handle)
        else:
            transaction.add(PERSON_KEY, handle, person.serialize(), None)
            transaction.person_del.append(str(handle))

    def get_del_func(self, key):
        key2del = {
            PERSON_KEY: self.del_person,
            FAMILY_KEY: self.del_family,
            SOURCE_KEY: self.del_source,
            EVENT_KEY:  self.del_event,
            MEDIA_KEY:  self.del_media,
            PLACE_KEY:  self.del_place,
            REPOSITORY_KEY: self.del_repository,
            NOTE_KEY:   self.del_note,
            }
        return key2del[key]

    def do_remove_object(self, handle, trans, dmap, key, del_list):
        if self.readonly or not handle:
            return

        handle = str(handle)
        self.delete_primary_from_reference_map(handle, trans)
        if trans.batch:
            del_func = self.get_del_func(key)
            del_func(handle)
        else:
            old_data = dmap.get(handle)
            trans.add(key, handle, old_data, None)
            del_list.append(handle)

    def remove_source(self, handle, transaction):
        """
        Remove the Source specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.source_map, 
                              SOURCE_KEY, transaction.source_del)

    def remove_event(self, handle, transaction):
        """
        Remove the Event specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.event_map, 
                              EVENT_KEY, transaction.event_del)

    def remove_object(self, handle, transaction):
        """
        Remove the MediaObjectPerson specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.media_map, 
                              MEDIA_KEY, transaction.media_del)

    def remove_place(self, handle, transaction):
        """
        Remove the Place specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.place_map, 
                              PLACE_KEY, transaction.place_del)

    def remove_family(self, handle, transaction):
        """
        Remove the Family specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.family_map, 
                              FAMILY_KEY, transaction.family_del)

    def remove_repository(self, handle, transaction):
        """
        Remove the Repository specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.repository_map, 
                              REPOSITORY_KEY, transaction.repository_del)

    def remove_note(self, handle, transaction):
        """
        Remove the Note specified by the database handle from the
        database, preserving the change in the passed transaction. 
        
        This method must be overridden in the derived class.
        """
        self.do_remove_object(handle, transaction, self.note_map, 
                              NOTE_KEY, transaction.note_del)

    def get_raw_person_data(self, handle):
        return self.person_map.get(str(handle))

    def get_raw_family_data(self, handle):
        return self.family_map.get(str(handle))

    def get_raw_object_data(self, handle):
        return self.media_map.get(str(handle))

    def get_raw_place_data(self, handle):
        return self.place_map.get(str(handle))

    def get_raw_event_data(self, handle):
        return self.event_map.get(str(handle))

    def get_raw_source_data(self, handle):
        return self.source_map.get(str(handle))

    def get_raw_repository_data(self, handle):
        return self.repository_map.get(str(handle))

    def get_raw_note_data(self, handle):
        return self.note_map.get(str(handle))

    def has_person_handle(self, handle):
        """
        Return True if the handle exists in the current Person database.
        """
        return str(handle) in self.person_map

    def has_event_handle(self, handle):
        """
        Return True if the handle exists in the current Event database.
        """
        return str(handle) in self.event_map

    def has_source_handle(self, handle):
        """
        Return True if the handle exists in the current Source database.
        """
        return str(handle) in self.source_map

    def has_place_handle(self, handle):
        """
        Return True if the handle exists in the current Place database.
        """
        return str(handle) in self.place_map

    def has_family_handle(self, handle):            
        """
        Return True if the handle exists in the current Family database.
        """
        return str(handle) in self.family_map

    def has_object_handle(self, handle):
        """
        Return True if the handle exists in the current MediaObjectdatabase.
        """
        return str(handle) in self.media_map

    def has_repository_handle(self, handle):
        """
        Return True if the handle exists in the current Repository database.
        """
        return str(handle) in self.repository_map

    def has_note_handle(self, handle):
        """
        Return True if the handle exists in the current Note database.
        """
        return str(handle) in self.note_map

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

    def __sortbymedia(self, first, second):
        media1 = self.media_map[str(first)][4]
        media2 = self.media_map[str(second)][4]
        return locale.strcoll(media1, media2)

    def __sortbymedia_key(self, key):
        media = self.media_map[str(key)][4]
        return locale.strxfrm(media)

    def set_mediapath(self, path):
        """Set the default media path for database, path should be utf-8."""
        if (self.metadata is not None) and (not self.readonly):
            self.metadata['mediapath'] = path

    def get_mediapath(self):
        """Return the default media path of the database."""
        if self.metadata is not None:
            return self.metadata.get('mediapath', None)
        return None

    def delete_primary_from_reference_map(self, handle, transaction):
        """
        Called each time an object is removed from the database. 
        
        This can be used by subclasses to update any additional index tables 
        that might need to be changed.
        """
        pass

    def update_reference_map(self, obj, transaction):
        """
        Called each time an object is writen to the database. 
        
        This can be used by subclasses to update any additional index tables 
        that might need to be changed.
        """
        pass

    def reindex_reference_map(self, callback):
        """
        Reindex all primary records in the database.
        """
        pass

    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.
        
        Returns an iterator over a list of (class_name, handle) tuples.

        @param handle: handle of the object to search for.
        @type handle: database handle
        @param include_classes: list of class names to include in the results.
                                Default: None means include all classes.
        @type include_classes: list of class names
        
        This default implementation does a sequential scan through all
        the primary object databases and is very slow. Backends can
        override this method to provide much faster implementations that
        make use of additional capabilities of the backend.

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use:

        >    result_list = list(find_backlink_handles(handle))
        """

        # Make a dictionary of the functions and classes that we need for
        # each of the primary object tables.
        primary_tables = {
            'Person': {'cursor_func': self.get_person_cursor, 
                       'class_func': Person}, 
            'Family': {'cursor_func': self.get_family_cursor, 
                       'class_func': Family}, 
            'Event': {'cursor_func': self.get_event_cursor, 
                      'class_func': Event}, 
            'Place': {'cursor_func': self.get_place_cursor, 
                      'class_func': Place}, 
            'Source': {'cursor_func': self.get_source_cursor, 
                       'class_func': Source}, 
            'MediaObject': {'cursor_func': self.get_media_cursor, 
                            'class_func': MediaObject}, 
            'Repository': {'cursor_func': self.get_repository_cursor, 
                           'class_func': Repository},
            'Note':   {'cursor_func': self.get_note_cursor, 
                       'class_func': Note},
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
        
class Transaction(object):
    """
    Define a group of database commits that define a single logical operation.
    """
    def __init__(self, msg, db, batch=False, no_magic=False):
        """
        Create a new transaction. 
        
        A Transaction instance should not be created directly, but by the 
        DbBase class or classes derived from DbBase. The db 
        parameter is a list-like interface that stores the commit data. This 
        could be a simple list, or a RECNO-style database object.

        The batch parameter is set to True for large transactions. For such
        transactions, the list of changes is not maintained, and no undo
        is possible.

        The no_magic parameter is ignored for non-batch transactions, and
        is also of no importance for DB backends other than BSD DB. For
        the BSDDB, when this paramter is set to True, some secondary
        indices will be removed at the beginning and then rebuilt at
        the end of such transaction (only if it is batch).
        """
        self.db = db
        self.first = None
        self.last = None
        self.batch = batch
        self.no_magic = no_magic
        self.length = 0
        self.timestamp = 0

        self.person_add = []
        self.person_del = []
        self.person_update = []

        self.family_add = []
        self.family_del = []
        self.family_update = []

        self.source_add = []
        self.source_del = []
        self.source_update = []

        self.event_add = []
        self.event_del = []
        self.event_update = []

        self.media_add = []
        self.media_del = []
        self.media_update = []

        self.place_add = []
        self.place_del = []
        self.place_update = []

        self.repository_add = []
        self.repository_del = []
        self.repository_update = []

        self.note_add = []
        self.note_del = []
        self.note_update = []

    def get_description(self):
        """
        Return the text string that describes the logical operation performed 
        by the Transaction.
        """
        return self.msg

    def set_description(self, msg):
        """
        Set the text string that describes the logical operation performed by 
        the Transaction.
        """
        self.msg = msg

    def add(self, obj_type, handle, old_data, new_data):
        """
        Add a commit operation to the Transaction. 
        
        The obj_type is a constant that indicates what type of PrimaryObject 
        is being added. The handle is the object's database handle, and the 
        data is the tuple returned by the object's serialize method.
        """
        self.last = self.db.append(
            cPickle.dumps((obj_type, handle, old_data, new_data), 1))
        if self.first is None:
            self.first = self.last

    def get_recnos(self):
        """
        Return a list of record numbers associated with the transaction.
        
        While the list is an arbitrary index of integers, it can be used
        to indicate record numbers for a database.
        """
        return range (self.first, self.last+1)

    def get_record(self, recno):
        """
        Return a tuple representing the PrimaryObject type, database handle
        for the PrimaryObject, and a tuple representing the data created by
        the object's serialize method.
        """
        return cPickle.loads(self.db[recno])

    def __len__(self):
        """
        Return the number of commits associated with the Transaction.
        """
        if self.last and self.first:
            return self.last - self.first + 1
        return 0
