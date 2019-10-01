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
    account_id=fields.Many2one('wip.account', string='WIP')
    location_id=fields.Many2one('stock.location', string='Location')
    state = fields.Selection([('new', 'New'), ('wip', 'WIP'),('posted_expense', 'Posted Expense')], default="new")
    stage = fields.Selection([('new', 'New'), ('wip', 'WIP'),('posted_expense', 'Posted Expense')], default="new")
    journal_siv_id=fields.Many2one('journal.siv', string='Journal')
    stock_picking_type_id=fields.Many2one('stock.picking.type' , string='Operation Type')
    
    
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
            if not rec.siv_job_id.analytic_account:
                raise UserError('There is no Analytic account assigned to Job')
            else:
                if rec.siv_line_ids:
                    for line in rec.siv_line_ids:
                        if line.product_id.categ_id.property_account_expense_categ_id and line.product_id.categ_id.product_account_contra_categ_id:
                            self.env['account.move'].create({'ref':'JE'+'-'+rec.name,
                                                                     'date': rec.date,
                                                                     'journal_id':self.env['account.journal'].search([('name','=','Miscellaneous Operations')]).id,
                                                                     'line_ids': [(0, 0, {
                                                                             'debit': 0.0,
                                                                             'credit': line.amount,
                                                                             'account_id': line.account_id.id,
                                                                             'analytic_account_id':rec.siv_job_id.analytic_account.id,
                                                                             'name':'Expense'}), 
                                                                             (0, 0, {
                                                                             'credit': 0.0,
                                                                             'debit':line.amount,
                                                                             'account_id': line.account_contra_id.id,
                                                                             'analytic_account_id':rec.siv_job_id.analytic_account.id,
                                                                             'name':'Contra'})]})
                            rec.write({'state':'posted_expense', 'stage':'posted_expense'})
                        else: 
                            raise UserError('Make sure product has expense and contra accounts')
                else:
                    raise UserError('There is no materials')
    
    @api.multi
    def post_je_mater(self):
        for rec in self:
            if not rec.siv_job_id.analytic_account:
                raise UserError('There is no Analytic account assigned to Job')
            else:
                if not rec.siv_line_ids:
                    raise UserError("There is no materials")
                else:
                    for line in rec.siv_line_ids:
                        if not line.product_id.categ_id.property_stock_valuation_account_id :
                            raise UserError("Make sure there is 'Stock Valuation Account for each line'")
                        else:
                            if not rec.account_id:
                                raise UserError("Make sure there is 'WIP Acct for SIV' ")
                            else:
                                self.env['account.move'].create({'ref':'JE-WIP'+'-'+rec.name,
                                                                         'date': rec.date,
                                                                         'journal_id':self.env['account.journal'].search([('name','=','Miscellaneous Operations')]).id,
                                                                         'line_ids': [(0, 0, {
                                                                                 'debit': 0.0,
                                                                                 'credit': line.amount,
                                                                                 'account_id': line.product_id.categ_id.property_stock_valuation_account_id.id,
                                                                                 'analytic_account_id':rec.siv_job_id.analytic_account.id,
                                                                                 'name':'Stock Valuation'}), 
                                                                                 (0, 0, {
                                                                                 'credit': 0.0,
                                                                                 'debit':line.amount,
                                                                                 'account_id': rec.account_id.id,
                                                                                 'analytic_account_id':rec.siv_job_id.analytic_account.id,
                                                                                 'name':'WIP'})]})
                                rec.write({'state':'wip', 'stage':'wip'})
            ir_seq_obj=self.env['ir.sequence']
            if not ir_seq_obj.name=='SSIV':
                    ir_seq_obj.create({'name':'SSIV',
                                       'implementation':'standard',
                                       'active':True,
                                       'prefix':'SSIV',
                                       'padding':0,
                                       'number_increment':1,
                                       'number_next_actual':0})
                    
            stock_pick_type_obj=self.env['stock.picking.type'].search([('name','=','Stock Issue Voucher')],limit=1)
            if not stock_pick_type_obj:
                ir_seq_obj=self.env['ir.sequence'].search([('name','=','SSIV')],limit=1)
                stock_loc_obj=self.env['stock.location'].search([('name','=','Stock'),('barcode','=','WH-STOCK')],limit=1)
                rec.stock_picking_type_id.create({'name':'Stock Issue Voucher',
                                                  'sequence_id':ir_seq_obj.id,
                                                  'code':'internal',
                                                  'show_reserved':True,
                                                  'default_location_dest_id':stock_loc_obj.id}) 
                rec.write({'stock_picking_type_id':self.env['stock.picking.type'].search([('name','=','Stock Issue Voucher')],limit=1).id})
            else:
                rec.write({'stock_picking_type_id':self.env['stock.picking.type'].search([('name','=','Stock Issue Voucher')],limit=1).id})
                
                
                

class SIVLine(models.Model):
    _name="siv.line"
    _description="Lines of SIV Rec"
    
    product_id = fields.Many2one('product.product',string='Code', required=True)
    product_inte_ref=fields.Char(string='Description', related='product_id.default_code')
#     quantity=fields.Integer()
    initial_demand=fields.Float()
#     reserved=fields.Integer(compute='_compute_reserved')
#     done=fields.Integer()
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
            
#     @api.one
#     @api.depends('initial_demand')
#     def _compute_reserved(self):
#         for rec in self:
#             stock_obj=self.env['stock.quant'].search([('product_id.default_code','=',rec.product_id.default_code),('quantity','>',0.0)],limit=1)
#             if stock_obj:
#                 result=stock_obj.quantity-(rec.initial_demand/2)
#                 stock_obj.write({'quantity':result})
#                 self.reserved=self.initial_demand
#         
                
                
                
                
                
                
                
                
                
                
                
                
                
                
    
    
    
    
    
    
    
    
    
    
    