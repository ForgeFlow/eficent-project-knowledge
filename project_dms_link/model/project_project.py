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

    def _get_url_dms_folder(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        directory_obj = self.pool.get('document.directory')
        project_model_id = self.pool.get('ir.model').search(
            cr, uid, [('model', '=', 'project.project')], context=context)
        for project in self.browse(cr, uid, ids, context=context):
            directory_ids = directory_obj.search(
                cr, uid, [('ressource_parent_type_id', '=', project_model_id),
                          ('ressource_id', '=', project.id)], context=context)
            for directory in directory_obj.browse(cr, uid, directory_ids,
                                                  context=context):
                res[project.id] = directory.url_dms
        return res

    _columns = {
        'url_dms_folder': fields.function(_get_url_dms_folder, method=True,
                                          type='text',
                                          string='URL of the folder in the '
                                                 'DMS')
    }