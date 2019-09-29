# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import Warning

class JobSIV(models.Model):
    _name='job.siv'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='SIV Related to Job'
    
    name=fields.Char('SIV No.')
    date=fields.Date(default=fields.Date.today())
    siv_job_id=fields.Many2one('manage.job',string='Job No.')
    job_description=fields.Char(string='Job Description', related='siv_job_id.description')
    siv_line_ids=fields.One2many('siv.line', 'job_siv_id')
    account_id=fields.Many2one('account.account', string='WIP')
    location_id=fields.Many2one('stock.location', string='Location')
    state = fields.Selection([('new', 'New'), ('posted', 'Posted')], default="new")
    stage = fields.Selection([('new', 'New'), ('posted', 'Posted')], default="new")
    
    @api.model
    def create(self, values):
        res = super(JobSIV, self).create(values)
        for val in res:
            val['name'] = self.env['ir.sequence'].next_by_code('siv.seq')
        return res
    
    @api.multi
    def post_je(self):
        """ Post SIV, and generate Jornal enteries"""
        for rec in self:
            if rec.siv_line_ids:
                for line in rec.siv_line_ids:
                    if line.product_id.categ_id.property_account_expense_categ_id and line.product_id.categ_id.product_account_contra_categ_id:
                        self.env['account.move'].create({'ref':'JE'+' '+rec.name,
                                                                 'date': rec.date,
                                                                 'journal_id':self.env['account.journal'].search([('name','=','Miscellaneous Operations')]).id,
                                                                 'line_ids': [(0, 0, {
                                                                         'debit': 0.0,
                                                                         'credit': line.amount,
                                                                         'account_id': line.account_id.id}), 
                                                                         (0, 0, {
                                                                         'credit': 0.0,
                                                                         'debit':line.amount,
                                                                         'account_id': line.account_contra_id.id})]})
                        rec.write({'state':'posted', 'stage':'posted'})
                    else: 
                        raise UserError('Make sure product has expense and contra accounts')
            else:
                raise UserError('There is no materials')
                

class SIVLine(models.Model):
    _name="siv.line"
    _description="Lines of SIV Rec"
    
    product_id = fields.Many2one('product.product',string='Code', required=True)
    product_inte_ref=fields.Char(string='Description', related='product_id.default_code')
#     quantity=fields.Integer()
    initial_demand=fields.Float()
    reserved=fields.Integer(compute='_compute_reserved')
    done=fields.Integer()
    currency_id = fields.Many2one('res.currency', string="Currency", related='product_id.currency_id')
    standard_price=fields.Float(string='Rate', related='product_id.standard_price')
    amount=fields.Monetary(compute='_compute_amount')
    job_siv_id=fields.Many2one('job.siv')
    account_id=fields.Many2one('account.account', string='Expense Acct', related='product_id.categ_id.property_account_expense_categ_id')
    account_contra_id=fields.Many2one('account.account', string='Contra Acct', related='product_id.categ_id.product_account_contra_categ_id')

    @api.depends('initial_demand','standard_price')
    def _compute_amount(self):
        for rec in self:
            rec.amount=rec.initial_demand*rec.standard_price
            
    @api.one
    @api.depends('initial_demand')
    def _compute_reserved(self):
        for rec in self:
            stock_obj=self.env['stock.quant'].search([('product_id.default_code','=',rec.product_id.default_code),('quantity','>',0.0)],limit=1)
            if stock_obj:
                result=stock_obj.quantity-(rec.initial_demand/2)
                stock_obj.write({'quantity':result})
                self.reserved=self.initial_demand
#         
                
                
                
                
                
                
                
                
                
                
                
                
                
                
    
    
    
    
    
    
    
    
    
    
    