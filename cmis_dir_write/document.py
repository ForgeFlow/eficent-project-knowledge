# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import hashlib
from openerp.osv import orm, fields
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job
import base64
from openerp import SUPERUSER_ID
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class cmis_object(orm.TransientModel):
    _name = 'cmis.object'

    _columns = {
        'name': fields.char('Object Name', size=256, required=True,
                            help='Object Name'),
        'title': fields.char('Object Title', size=256, required=False,
                             help='Object Title'),
        'content_stream_mime_type': fields.char('Mime Type', size=256,
                                                required=False,
                                                help='Mime Type'),
        'base_type': fields.char('Base Type', size=256, required=True,
                                 help='Base Type'),
        'creation_date': fields.char('Creation Date', size=32,
                                     required=False, help='Creation Date'),
    }


class document_directory(orm.Model):
    _inherit = 'document.directory'

    def _get_url_dms_folder(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        cmis_backend_obj = self.pool.get('cmis.backend')
        # login with the cmis account
        backend_ids = cmis_backend_obj.search(cr, uid, [], context=context)
        if not backend_ids:
            return res
        repo = cmis_backend_obj._auth(cr, uid, backend_ids, context=context)
        cmis_backend = cmis_backend_obj.browse(cr, uid, backend_ids[0],
                                               context=context)
        if not cmis_backend.navigation_path:
            return res
        for directory in self.browse(cr, uid, ids, context=context):
            if directory.id_dms:
                folder = repo.getObject(directory.id_dms)
                props = folder.properties
                url = cmis_backend.navigation_path + props['cmis:path']
                res[directory.id] = url
        return res

    def _get_cmis_objects(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        cmis_backend_obj = self.pool.get('cmis.backend')
        cmis_object_obj = self.pool.get('cmis.object')
        # login with the cmis account
        backend_ids = cmis_backend_obj.search(cr, uid, [], context=context)
        if not backend_ids:
            return res
        repo = cmis_backend_obj._auth(cr, uid, backend_ids, context=context)
        for directory in self.browse(cr, uid, ids, context=context):
            if directory.id_dms:
                folder = repo.getObject(directory.id_dms)
                dms_obj_ids = []
                for child in folder.getChildren():
                    props = child.properties
                    vals = {
                        'name': child.name,
                        'title': child.title,
                        'content_stream_mime_type': props.get(
                            'cmis:contentStreamMimeType', False),
                        'creation_date': props.get(
                            'cmis:creationDate', False),
                        'base_type': props.get(
                            'cmis:baseTypeId', False),
                    }

                    dms_obj_ids.append(cmis_object_obj.create(
                        cr, uid, vals, context=context))
                res[directory.id] = dms_obj_ids
        return res

    _columns = {
        'id_dms': fields.char('Id of Dms', size=256, help="Id of Dms."),
        'url_dms': fields.function(_get_url_dms_folder, method=True,
                                   type='text',
                                   string='URL of the folder in the DMS'),
        'cmis_objects': fields.function(_get_cmis_objects, method=True,
                                       type='one2many', obj='cmis.object',
                                       string='DMS Objects',
                                       readonly=True),
    }

    def create(self, cr, uid, values, context=None):
        cmis_backend_obj = self.pool.get('cmis.backend')
        user_obj = self.pool.get('res.users')
        directory_obj = self.pool.get('document.directory')
        dir_id = super(document_directory, self).create(cr, uid, values,
                                                        context=context)
        # login with the cmis account
        backend_ids = cmis_backend_obj.search(cr, uid, [], context=context)
        repo = cmis_backend_obj._auth(cr, uid, backend_ids, context=context)
        user_login = user_obj.browse(cr, uid, uid, context=context).login
        if not backend_ids:
            return dir_id
        cmis_backend = cmis_backend_obj.browse(cr, uid, backend_ids[0],
                                               context=context)
        folder_path = cmis_backend.initial_directory_write

        if folder_path:
            folder = repo.getObjectByPath(folder_path)
        else:
            folder = repo.rootFolder

        if 'parent_id' in values and values['parent_id']:
            parent_dir = directory_obj.browse(cr, uid, values['parent_id'],
                                              context=context)
            if parent_dir.id_dms:
                folder = repo.getObject(parent_dir.id_dms)
        try:
            NewFolder = folder.createFolder(values['name'])
        except Exception, e:
            raise orm.except_orm(_('Error'),
                                 _('Cannot create the folder in the '
                                   'DMS.\n'
                                   '(%s') % e)

        # TODO: create custom properties on a document (Alfresco)
        # someDoc.getProperties().update(props)
        # Updating ir.attachment object with the new id
        # of document generated by DMS
        self.write(cr, uid, dir_id, {
            'id_dms': NewFolder.getObjectId()}, context=context)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cmis_backend_obj = self.pool.get('cmis.backend')
        user_obj = self.pool.get('res.users')
        directory_obj = self.pool.get('document.directory')
        # login with the cmis account
        backend_ids = cmis_backend_obj.search(cr, uid, [], context=context)
        repo = cmis_backend_obj._auth(cr, uid, backend_ids, context=context)
        super(document_directory, self).write(cr, uid, ids, vals,
                                              context=context)
        cmis_backend = cmis_backend_obj.browse(cr, uid, backend_ids[0],
                                               context=context)
        folder_path = cmis_backend.initial_directory_write

        for dir in self.browse(cr, uid, ids, context=context):
            if dir.id_dms:
                dms_folder = repo.getObject(dir.id_dms)
                if 'parent_id' in vals:
                    current_parent = dms_folder.getParent()
                    if vals['parent_id']:
                        parent_dir = directory_obj.browse(
                            cr, uid, vals['parent_id'], context=context)
                        if parent_dir.id_dms:
                            new_parent = repo.getObject(parent_dir.id_dms)
                        else:
                            if folder_path:
                                new_parent = repo.getObjectByPath(folder_path)
                            else:
                                new_parent = repo.rootFolder
                        dms_folder.move(current_parent, new_parent)
                if 'name' in vals:
                    props = {
                        'cmis:name': vals['name'],
                    }
                    dms_folder.updateProperties(props)
        return True

    def unlink(self, cr, uid, ids, context=None):
        cmis_backend_obj = self.pool.get('cmis.backend')
        # login with the cmis account
        backend_ids = cmis_backend_obj.search(cr, uid, [], context=context)
        repo = cmis_backend_obj._auth(cr, uid, backend_ids, context=context)
        for folder in self.read(cr, uid, ids, ['id', 'id_dms'],
                                context=context):
            super(document_directory, self).unlink(cr, uid, folder['id'],
                                                   context=context)
            id_dms = folder['id_dms']
            if id_dms:
                # Get results from id of document
                object = repo.getObject(id_dms)
                try:
                    object.delete()
                except Exception, e:
                    raise orm.except_orm(_('Error'),
                                         _('Cannot delete the folder in the '
                                           'DMS.\n'
                                           '(%s') % e)