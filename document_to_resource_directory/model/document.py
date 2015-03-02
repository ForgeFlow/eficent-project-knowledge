# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester<jordi.ballester@eficent.com>
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

from openerp.osv import fields, orm


class document_directory(orm.Model):
    _inherit = 'document.directory'

    _sql_constraints = [
        ('dir_uniq', 'unique (ressource_id,ressource_parent_type_id)',
         'The directory name must be unique per resource type and resource !'),
    ]


class document_file(orm.Model):
    _inherit = 'ir.attachment'

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        directory_obj = self.pool.get('document.directory')
        directory_ids = directory_obj.search(
            cr, uid,
            [('ressource_parent_type_id', '=', vals['res_model']),
             ('ressource_id', '=', vals['res_id'])], context=context)
        if directory_ids:
            context['parent_id'] = directory_ids[0]
        #else:
        #    root_model, root_id = self.pool.get(
        #        'ir.model.data').get_object_reference(
        #        cr, uid, 'document', 'dir_root')
        #    context['parent_id'] = root_id

        return super(document_file, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        directory_obj = self.pool.get('document.directory')
        parent_dir_id = vals.get('parent_id', False)
        if 'parent_id' in vals:
            if vals['parent_id']:
                parent_dir = directory_obj.browse(cr, uid, parent_dir_id,
                                                  context=context)
                if parent_dir.ressource_parent_type_id \
                        and parent_dir.ressource_id:
                    vals['res_model'] = \
                        parent_dir.ressource_parent_type_id.model
                    vals['res_id'] = parent_dir.ressource_id
                else:
                    vals['res_model'] = False
                    vals['res_id'] = False
            else:
                old_docs = self.read(cr, uid, ids, ['parent_id'],
                                     context=context)
                for old_doc in old_docs:
                    if old_doc['parent_id']:
                        new_vals = {}
                        new_vals['res_model'] = False
                        new_vals['res_id'] = False
                        self.write(cr, uid, old_doc['id'], new_vals,
                                   context=context)
        return super(document_file, self).write(cr, uid, ids, vals, context)
