# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class PettyCash(models.Model):
    _name='petty.cash'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='Petty Cash Management'
    
    name = fields.Char(readonly=True)
    start_date = fields.Datetime(string='Start Date', default=datetime.today())
    expected_date = fields.Datetime(string='Expected Date') 
    resposible_id=fields.Many2one('res.users', string='Responsible User')
    Treasurer_id=fields.Many2one('res.users', string='Treasurer', default=lambda self: self.env.user)
    allowed_expenses=fields.Many2many('petty.cash.type', string='Type')

#   Openning balance fields 
    currency_id = fields.Many2one('res.currency', string="Currency")
    amount = fields.Monetary()
    opening_date=fields.Date('Opening Date')
    type=fields.Selection([
                          ('cash','Cash'),
                          ('chque','Chque')], string='Type')
    chque_no=fields.Integer('Chque No')
    bank_id=fields.Many2one('res.partner.bank', string='Bank')
    remain_balance = fields.Monetary('Remaining Balance', compute='_calculate_remaining_balance')
#   ids
    petty_cash_line_ids=fields.One2many('petty.cash.line', 'petty_cash_id')  
    
    @api.model
    def create(self, values):
        res = super(PettyCash, self).create(values)
        for val in res:
            val['name'] = self.env['ir.sequence'].next_by_code('petty.seq')
        return res
    @api.depends('amount')
    def _calculate_remaining_balance(self):
        for rec in self:
            rec.remain_balance=rec.amount-sum(rec.petty_cash_line_ids.mapped('cost'))
    
class PettyCashType(models.Model):
    _name='petty.cash.type'
    _description='Petty Cash Type'
    
    name=fields.Char('Name')
    
class PettyCashLine(models.Model):
    _name='petty.cash.line'
    _description='Petty Cash Line Model'
    
    product_id = fields.Many2one('product.product', required=True)
    petty_cash_id=fields.Many2one('petty.cash')
    analytic_account = fields.Many2one('account.analytic.account', string='Analytical Account')
    attachment=fields.Binary('Attachment')
    date_time=fields.Datetime('Date')
    allowed_expenses_ids=fields.Many2many('petty.cash.type', string='Type')
    allowed_expenses_ids_com=fields.Many2many('petty.cash.type', related='petty_cash_id.allowed_expenses')
    cost=fields.Float()
    