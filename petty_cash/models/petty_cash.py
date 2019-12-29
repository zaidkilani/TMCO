# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit='account.move'
    
    petty_id = fields.Many2one('petty.cash',copy=False)
    
    
class PettyCash(models.Model):
    _name='petty.cash'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='Petty Cash Management'
    
    name = fields.Char(readonly=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.today(),required=True)
    expected_date = fields.Date(string='Expected Date') 
    resposible_id=fields.Many2one('res.users', string='Responsible User',required=True)
    Treasurer_id=fields.Many2one('res.users', string='Treasurer', default=lambda self: self.env.user)
    allowed_expenses=fields.Many2many('petty.cash.type', string='Type',required=True)
    journal_id = fields.Many2one('account.journal','Jouranl',required=True)
    account_id = fields.Many2one('account.account','Responsible User Account',required=True)
    move_id = fields.Many2one('account.move','Move',readonly=True,copy=False)
    state = fields.Selection([('open','Open'),('closed','Closed')],default='open',copy=False)
    posted = fields.Boolean(copy=False)
    

#   Openning balance fields 
    currency_id = fields.Many2one('res.currency', string="Currency")
    amount = fields.Monetary(required=True)
    actual_close_bal= fields.Monetary()
    diffrence_bal= fields.Monetary(compute='_compute_diff_balc')
    opening_date=fields.Date('Opening Date')
    type=fields.Selection([
                          ('cash','Cash'),
                          ('chque','Chque')], string='Type')
    chque_no=fields.Integer('Chque No')
    bank_id=fields.Many2one('res.partner.bank', string='Bank')
    remain_balance = fields.Monetary('Remaining Balance', compute='_calculate_remaining_balance')
    
#   ids
    petty_cash_line_ids=fields.One2many('petty.cash.line', 'petty_cash_id')  
    @api.multi
    def write(self,vals):
        if 'closed' in self.mapped('state'):
            raise UserError('You cannot modify closed petty cash')
        return super(PettyCash, self).write(vals)
    @api.depends('amount','actual_close_bal')
    def _compute_diff_balc(self):
        for rec in self:
            rec.diffrence_bal=rec.remain_balance - rec.actual_close_bal
            
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
    
    def create_start_journal(self):
        vals = {'date':self.start_date,
                'petty_id':self.id,
                'journal_id':self.journal_id.id,
                'ref':'Deposit of petty cash ' + self.name,
                'line_ids':[(0,0,{'account_id':self.account_id.id,
                                  'debit':self.amount}),
                            (0,0,{'account_id':self.allowed_expenses.account_id.id,
                                  'credit':self.amount})]}
        self.move_id = self.env['account.move'].create(vals).id
    def settle_je(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['view_mode'] = 'form'
        action['views'] = [action['views'][2]]
        action['context'] = "{'view_no_maturity': True,'default_petty_id':%s}"%self.id
        return action
    
    def open_je_view(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['context'] = "{'view_no_maturity': True,'default_petty_id':%s}"%self.id
        action['domain'] = [('petty_id','=',self.id)]
        return action
    
        
    def post_expenses(self):
        self.posted = True
        self.expected_date = fields.Date.today()
        vals = {'date':self.expected_date,
                'journal_id':self.journal_id.id,
                'ref':'Expens of petty cash ' + self.name,
                'line_ids':[],
                'petty_id':self.id}
        lines = []
        cost = 0
        for line in self.petty_cash_line_ids:
            lines.append((0,0,{'account_id':line.product_id.property_account_expense_id.id,
                                  'debit':line.cost,
                                  'analytic_account_id':line.analytic_account.id}))
            cost+=line.cost
        lines.append((0,0,{'account_id':self.account_id.id,
                                  'credit':cost}))
        vals['line_ids'] = lines
        self.env['account.move'].create(vals)
        
    def settle(self):
        if self.diffrence_bal == 0.0:
            self.state = 'closed'
        else:
            raise UserError("Please adjust actual closing balance")
            
            
            
    def issue_report(self):
        return self.env.ref('petty_cash.issue_report').report_action(self.ids)
    
    
    def main_report(self):
        return self.env.ref('petty_cash.main_report').report_action(self.ids)
    
    def main_report(self):
        return self.env.ref('petty_cash.close_report').report_action(self.ids)
    
    
    
class PettyCashType(models.Model):
    _name='petty.cash.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='Petty Cash Type'
    
    name=fields.Char('Name',required=True)
    active=fields.Boolean(default=True)
    account_id = fields.Many2one('account.account','Main Cash Account',required=True)
    
    
class PettyCashLine(models.Model):
    _name='petty.cash.line'
    _description='Petty Cash Line Model'
    
    product_id = fields.Many2one('product.product', required=True)
    petty_cash_id=fields.Many2one('petty.cash')
    analytic_account = fields.Many2one('account.analytic.account', string='Analytical Account')
    attachement_ids = fields.Many2many('ir.attachment', string="Attachment Doc")
    date_time=fields.Date('Date')
    allowed_expenses_ids=fields.Many2many('petty.cash.type', string='Type')
    allowed_expenses_ids_com=fields.Many2many('petty.cash.type', related='petty_cash_id.allowed_expenses')
    cost=fields.Monetary()
    bill_no=fields.Char('Bill No.')
    vendor_name=fields.Char('Vendor Name')
    currency_id = fields.Many2one('res.currency', string="Currency", related='petty_cash_id.currency_id')

    
    