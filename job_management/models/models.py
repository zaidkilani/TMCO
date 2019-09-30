# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit='product.category'
    _decription='product.category'
    
    product_account_contra_categ_id=fields.Many2one('account.account', string='Contra Account')
    
class StockQuant(models.Model):
    _inherit='stock.quant'
    _decription='product.category quant'

class WipAccount(models.Model):
    _name='wip.account'
    _description='WIP Account for SIV'
    
    name=fields.Char()
    account_id=fields.Many2one('account.account', string='WIP')

class JournalSiv(models.Model):
    _name='journal.siv'
    _description='journal siv'
    
    name=fields.Char()
    journal_id=fields.Many2one('account.journal', string='Journal')