# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AaccountAssetAsset(models.Model):
    _inherit='account.asset.asset'
    
    total_value = fields.Float('Depreciated',store=True,compute="_compute_total_value")
    
    @api.depends('depreciation_line_ids','depreciation_line_ids.depreciated_value')
    def _compute_total_value(self):
        for rec in self:
            rec.total_value = sum(rec.mapped('depreciation_line_ids.depreciated_value'))
        
class StockQuant(models.Model):
    _inherit='stock.quant'
    
    cost = fields.Float('Cost',related='product_id.standard_price',store=True)
    total_cost = fields.Float('Total Cost',compute='_compute_total_cost')
    
    @api.depends('cost','quantity')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.cost * rec.quantity
            
    
   