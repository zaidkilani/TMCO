# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StockQuant(models.Model):
    _inherit='stock.quant'
    
    cost = fields.Float('Cost',related='product_id.standard_price',store=True)
    total_cost = fields.Float('Total Cost',compute='_compute_total_cost')
    
    @api.depends('cost','quantity')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.cost * rec.quantity
            
    
   