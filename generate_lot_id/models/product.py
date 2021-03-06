from odoo import api, fields, models, _

from datetime import datetime
from dateutil import tz

from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

import string
import re
import logging

class ProductTemplate(models.Model):
    _inherit = "product.template"
    lot_abbv = fields.Char('Lot Code Format', help='To assist with manufacturing, '
                                'lot codes will automatically generate with this prefix.\n'
                                'You can add other pieces to be generated, such as \n'
                                '- [DATE]\n yyyymmdd'
                               '- [JULIAN] - Julian date code\n'
                               '- [JULIAN_DAY] - Julian day\n'
                               '- [YEARYY] - Last two digits of year\n'
                               '- [MONTH] - 01-12 Month\n'
                               '- [MM] - 01-12 Month\n' 
                               '- [DAY] - 01-31 Day\n'
                               '- [DD] - 01-31 Day\n' 
                               '- [YEAR] - Full year\n' 
                               '- [YY] - Full year\n' 
                               '-[YYMMDD] - YearMonthDay\n'
                               '-[DDMMYY] - DayMonthYear\n'
                               '-[MMDDYY] - MonthDayYear\n'
                                '- [OPERATION_CODE] - Manufacturing Operation Code\n'                                
                                '- [WAREHOUSE_CODE] - Warehouse Code\n'
                                '- [USER_DEFINED] - Variable will be entered by user when creating lot\n'         
                                'For example, CCSS-[JULIAN_DAY]-[YEARYY] will output the Julian datecode: CCSS-19118\n'
                                'Add an extra underscore to offer employees tips on the user defined variable, \n'
                                'such as [USER_DEFINED_MACHINE_NUMBER], will print "Machine Number" below the field.\n')

class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    select_lot_ids = fields.Many2many('stock.production.lot', string='Select Lot Codes', store=False, create_edit=False, help='Select a lot code to add to this workorder.')

class ProductProduct(models.Model):
    _inherit = "product.product"
    last_lot_idx = fields.Char('Last lot index', help='Returns Last idx')

    @api.model
    def gen_lot_code(self, user_defined='', gen_date=datetime.now()):
        if self.lot_abbv is False:
            # If no format is specified.
            julian = '%d%03d' % (gen_date.timetuple().tm_year, gen_date.timetuple().tm_yday)
            if self.default_code is not False:
                return str(self.default_code) + str('-') + julian
            else:
                return julian

        if self.env.context.get('tz', False):
            gen_date = gen_date.replace(tzinfo=tz.tzutc())
            gen_date = gen_date.astimezone(tz.gettz(self.env.context['tz']))

        lot_name = self.lot_abbv
        if "[000]" in lot_name:
            cr = self.env.cr
            sql = """
                    SELECT last_lot_idx FROM product_product
                    where last_lot_idx is not NULL
                    ORDER BY last_lot_idx DESC  """
            cr.execute(sql)
            response = cr.dictfetchall()
            _logger = logging.getLogger(__name__)
            logging.info(response)
            logging.info(self.id)
            if len(response) > 0:
                last_index = response[0]['last_lot_idx']
                if last_index is None:
                    last_index = "001"
                else:
                    last_index = int(last_index) + 1
                    if last_index < 10:
                        last_index = "00" + str(last_index)
                    elif last_index >= 10 and last_index <= 99:
                        last_index = "0" + str(last_index)
                    else:
                        last_index = str(last_index)
                lot_name = str.replace(lot_name, '[000]', last_index, 1)
                self.env.cr.execute(f"""
                                    Update  product_product
                                    SET last_lot_idx= '{last_index}'
                                    where id = '{self.id}'
                                    """)




            else:
                lot_name = str.replace(lot_name, '[000]', "001", 1)
                self.env.cr.execute(f"""
                                                    Update  product_product
                                                    SET last_lot_idx= '002'
                                                    where id = '{self.id}'
                                                    """)

        lot_name = str.replace(lot_name, '[JULIAN]',
                               '%d%03d' % (gen_date.timetuple().tm_year, gen_date.timetuple().tm_yday), 1)
        lot_name = str.replace(lot_name, '[JULIAN_DAY]', str(gen_date.timetuple().tm_yday).zfill(3), 1)
        lot_name = str.replace(lot_name, '[YEARYY]', gen_date.strftime("%y"), 1)
        lot_name = str.replace(lot_name, '[YEAR]', gen_date.strftime("%Y"), 1)
        lot_name = str.replace(lot_name, '[YYYY]', gen_date.strftime("%Y"), 1)
        lot_name = str.replace(lot_name, '[yyyy]', gen_date.strftime("%Y"), 1)
        lot_name = str.replace(lot_name, '[STATION_CODE]', '', 1)
        lot_name = str.replace(lot_name, '[DATE]', fields.Date.to_string(gen_date), 1)

        lot_name = str.replace(lot_name, '[MMDDYY]',
                               gen_date.strftime("%m").zfill(2) + gen_date.strftime("%d").zfill(2) + gen_date.strftime(
                                   "%Y"), 1)
        lot_name = str.replace(lot_name, '[DDMMYY]',
                               gen_date.strftime("%d").zfill(2) + gen_date.strftime("%m").zfill(2) + gen_date.strftime(
                                   "%Y"), 1)
        lot_name = str.replace(lot_name, '[YYMMDD]',
                               gen_date.strftime("%Y") + gen_date.strftime("%m").zfill(2) + gen_date.strftime(
                                   "%d").zfill(2), 1)

        lot_name = str.replace(lot_name, '[DAY]', gen_date.strftime("%d").zfill(2), 1)
        lot_name = str.replace(lot_name, '[DD]', gen_date.strftime("%d").zfill(2), 1)
        lot_name = str.replace(lot_name, '[dd]', gen_date.strftime("%d").zfill(2), 1)
        lot_name = str.replace(lot_name, '[MONTH]', gen_date.strftime("%m").zfill(2), 1)
        lot_name = str.replace(lot_name, '[MM]', gen_date.strftime("%m").zfill(2), 1)
        lot_name = str.replace(lot_name, '[mm]', gen_date.strftime("%m").zfill(2), 1)
        lot_name = str.replace(lot_name, '[SECOND]', gen_date.strftime("%S").zfill(2), 1)
        lot_name = str.replace(lot_name, '[HOUR]', gen_date.strftime("%H").zfill(2), 1)
        lot_name = str.replace(lot_name, '[MINUTE]', gen_date.strftime("%M").zfill(2), 1)

        # TODO: implement STATION_CODE and WAREHOUSE_CODE
        # lot_name = str.replace(lot_name, '[STATION_CODE]', '', 1)

        context = dict(self._context or {})

        if context.get('default_workorder_id', False) is not False:
            workorder_id = self.env['mrp.workorder'].browse(context.get('default_workorder_id', False))
            if workorder_id.production_id.picking_type_id.lot_abbv:
                lot_name = str.replace(lot_name, '[OPERATION_CODE]',
                                       workorder_id.production_id.picking_type_id.lot_abbv, 1)
            if workorder_id.production_id.picking_type_id.warehouse_id.lot_abbv:
                lot_name = str.replace(lot_name, '[WAREHOUSE_CODE]',
                                       workorder_id.production_id.picking_type_id.warehouse_id.lot_abbv, 1)
            if workorder_id.workcenter_id.lot_abbv:
                lot_name = str.replace(lot_name, '[WORKCENTER_CODE]', workorder_id.workcenter_id.lot_abbv, 1)
        if context.get('default_production_id', False) is not False:
            production_id = self.env['mrp.production'].browse(context.get('default_production_id', False))
            if production_id.picking_type_id.lot_abbv:
                lot_name = str.replace(lot_name, '[OPERATION_CODE]', production_id.picking_type_id.lot_abbv, 1)
            if production_id.picking_type_id.warehouse_id.lot_abbv:
                lot_name = str.replace(lot_name, '[WAREHOUSE_CODE]',
                                       production_id.picking_type_id.warehouse_id.lot_abbv, 1)
            # If on a production order, we should only do it if there is one workorder, one workcenter..
            if len(production_id.workorder_ids) == 1 and production_id.workorder_ids.workcenter_id.lot_abbv:
                lot_name = str.replace(lot_name, '[WORKCENTER_CODE]',
                                       production_id.workorder_ids.workcenter_id.lot_abbv, 1)

        if user_defined:
            # lot_name = str.replace(lot_name, '[USER_DEFINED]', user_defined, 1)
            lot_name = self._regex(lotcode=lot_name, search=r'\[USER_DEFINED_?[\w_]*\]', user_defined=user_defined)

        # TODO: Replace any sequential dashes with single dashes.
        return lot_name

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_generate_serial(self):
        self.ensure_one()

        self.lot_producing_id = self.env['stock.production.lot'].create({
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'name': self.product_id.gen_lot_code(),
        })
        if self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_line_ids:
            self.move_finished_ids.filtered(
                lambda m: m.product_id == self.product_id).move_line_ids.lot_id = self.lot_producing_id
        if self.product_id.tracking == 'serial':
            self._set_qty_producing()
