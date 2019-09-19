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
    
    @api.model
    def create(self, values):
        res = super(PettyCash, self).create(values)
        for val in res:
            val['name'] = self.env['ir.sequence'].next_by_code('petty.seq')
        return res
    
class PettyCashType(models.Model):
    _name='petty.cash.type'
    _description='Petty Cash Type'
    
    name=fields.Char('Name')
    
#     @api.model
#     def create(self, values):
#         res = super(Job, self).create(values)
#         for val in res:
#             val['name'] = self.env['ir.sequence'].next_by_code('job.seq')
#         for rec in res:
#             if not rec.analytic_account:
#                 rec.ensure_one()
#                 rec.analytic_account.create({'name':rec.name,
#                                              'code':rec.name})
#                 ana_acct_obj = rec.env['account.analytic.account'].search([('name','=',rec.name)])
#                 rec.write({'analytic_account':ana_acct_obj.id})
#                 rec.message_post(body="Analytic account has been added")
#             else:
#                 raise UserError("This 'Job' is already assigned to an 'Analytic account'.")
#         return res