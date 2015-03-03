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


class project_project(orm.Model):
    _inherit = 'project.project'

    def _get_directory_cmis_data(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        directory_obj = self.pool.get('document.directory')
        project_model_id = self.pool.get('ir.model').search(
            cr, uid, [('model', '=', 'project.project')], context=context)
        for project in self.browse(cr, uid, ids, context=context):
            directory_ids = directory_obj.search(
                cr, uid, [('ressource_parent_type_id', '=',
                           project_model_id[0]),
                          ('ressource_id', '=', project.id)], context=context)
            for directory in directory_obj.browse(cr, uid, directory_ids,
                                                  context=context):
                cmis_object_ids = []
                for cmis_object in directory.cmis_objects:
                    cmis_object_ids.append(cmis_object.id)

                res[project.id] = {
                    'dms_folder_url': directory.url_dms,
                    'dms_cmis_folder_objects': cmis_object_ids,
                }
        return res

    _columns = {
        'dms_folder_url': fields.function(_get_directory_cmis_data,
                                          multi='cmis',
                                          method=True,
                                          type='text',
                                          string='URL of the folder in the '
                                                 'DMS'),
        'dms_cmis_folder_objects': fields.function(_get_directory_cmis_data,
                                                   method=True,
                                                   multi='cmis',
                                                   type='one2many',
                                                   obj='cmis.object',
                                                   string='DMS Objects',
                                                   readonly=True),
    }