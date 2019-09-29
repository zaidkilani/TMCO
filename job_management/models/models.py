# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit='product.category'
    _decription='product.category'
    
    product_account_contra_categ_id=fields.Many2one('account.account', string='Contra Account')
    
class StockQuant(models.Model):
    _inherit='stock.quant'
    _decription='product.category quant'