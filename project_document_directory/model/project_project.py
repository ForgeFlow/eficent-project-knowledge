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
import decimal_precision as dp
from openerp.osv import fields, orm


class project_project(orm.Model):
    _inherit = 'project.project'

    def create(self, cr, uid, vals, context=None):
        project_id = super(project_project, self).create(
            cr, uid, vals, context=context)
        parent_dir_id = False
        directory_obj = self.pool.get('document.directory')
        project_obj = self.pool.get('project.project')
        project_model_id = self.pool.get('ir.model').search(
            cr, uid, [('model', '=', 'project.project')],
            context=context)[0]
        if vals.get('parent_id', False):
            project_ids = project_obj.search(
                cr, uid, [('analytic_account_id', '=', vals['parent_id'])],
                context=context)
            if project_ids:
                parent_dir_ids = directory_obj.search(
                    cr, uid, [
                        ('ressource_id', '=', project_ids[0]),
                        ('ressource_parent_type_id', '=',
                         project_model_id)], context=context)
                if parent_dir_ids:
                    parent_dir_id = parent_dir_ids[0]
            else:
                root_type, root_id = \
                    self.pool.get('ir.model.data').get_object_reference(
                        cr, uid, 'document', 'dir_root')
                parent_dir_id = root_id

        dir_vals = {
            'name': vals['name'],
            'parent_id': parent_dir_id,
            'ressource_id': project_id,
            'ressource_parent_type_id': project_model_id,
            'resource_find_all': False,
        }

        directory_obj.create(cr, uid, dir_vals, context=context)
        return project_id

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        directory_obj = self.pool.get('document.directory')
        project_obj = self.pool.get('project.project')
        project_model_id = self.pool.get('ir.model').search(
            cr, uid, [('model', '=', 'project.project')],
            context=context)
        for project in self.browse(cr, uid, ids, context=context):
            dir_ids = directory_obj.search(
                cr, uid, [
                    ('ressource_id', '=', project.id),
                    ('ressource_parent_type_id', '=',
                     project_model_id)], context=context)
            if not dir_ids:
                continue
            dir_vals = {}
            if 'name' in vals:
                dir_vals.update({'name': vals['name']})
            if 'parent_id' in vals:
                root_type, root_id = \
                    self.pool.get('ir.model.data').get_object_reference(
                        cr, uid, 'document', 'dir_root')
                parent_dir = root_id
                if vals['parent_id']:
                    parent_project_ids = project_obj.search(
                        cr, uid,
                        [('analytic_account_id', '=', vals['parent_id'])],
                        context=context)
                    if parent_project_ids:
                        parent_dir_ids = directory_obj.search(
                            cr, uid, [
                                ('ressource_id', '=',
                                 parent_project_ids[0]),
                                ('ressource_parent_type_id', '=',
                                 project_model_id)], context=context)
                        parent_dir = parent_dir_ids[0]

                dir_vals.update({'parent_id': parent_dir})

            directory_obj.write(cr, uid, dir_ids, dir_vals,
                                context=context)

        return super(project_project, self).write(
            cr, uid, ids, vals, context=context)