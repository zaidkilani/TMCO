# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class PurchaseOrder(models.Model):
    _inherit='purchase.order.line'
    
    @api.onchange('product_id')
    def update_price_unit(self):
        for rec in self.filtered('product_id'):
            pol_id = self.env['purchase.order.line'].search([('product_id','=',rec.product_id.id)],order='id desc', limit=1)
            if pol_id:
                rec.price_unit = pol_id.price_unit
            else:
                rec.standard_price = 0
    
    

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
    location_id=fields.Many2one('stock.location', string='Location', related='siv_job_id.location_pro_id')
    state = fields.Selection([('new', 'New'), ('wip', 'WIP'),('prod_trans', 'Production Transfer'),('posted_expense', 'Posted Expense')], default="new")
    stage = fields.Selection([('new', 'New'), ('wip', 'WIP'),('prod_trans', 'Production Transfer'),('posted_expense', 'Posted Expense')], default="new")
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
        self.post_je_mater()
        self.production_move()
        """ Post SIV, and generate Jornal enteries"""
        for rec in self:
            if not rec.siv_job_id.analytic_account:
                raise UserError('There is no Analytic account assigned to Job')
            else:
                if rec.siv_line_ids:
                    for line in rec.siv_line_ids:
                        if line.product_id.categ_id.product_account_exp_siv_id and line.product_id.categ_id.product_account_contra_categ_id:
                            self.env['account.move'].create({'ref':'JE'+'-'+rec.name,
                                                                     'date': rec.date,
                                                                     'journal_id':self.env['account.journal'].search([('name','=','Miscellaneous Operations')]).id,
                                                                     'line_ids': [(0, 0, {
                                                                             'debit': 0.0,
                                                                             'credit': line.amount,
                                                                             'account_id': line.account_id.id,
                                                                             'name':'Expense'}), 
                                                                             (0, 0, {
                                                                             'credit': 0.0,
                                                                             'debit':line.amount,
                                                                             'account_id': line.account_contra_id.id,
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
                                                                                 'account_id': line.product_id.categ_id.property_stock_account_output_categ_id.id,
                                                                                 'name':'Stock Valuation'}), 
                                                                                 (0, 0, {
                                                                                 'credit': 0.0,
                                                                                 'debit':line.amount,
                                                                                 'account_id': wip.account.account_id,
                                                                                 'analytic_account_id':rec.siv_job_id.analytic_account.id,
                                                                                 'name':'WIP'})]})
                                rec.write({'state':'wip', 'stage':'wip'})
            ir_seq_obj=self.env['ir.sequence'].search([('name','=','SSIV')],limit=1)
            if not ir_seq_obj:
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
                stock_loc_obj=self.env['stock.location'].search([('name','=','OUT'),('barcode','=','WH-OUT')],limit=1)
                stock_loc_src_obj=self.env['stock.location'].search([('name','=','STOCK'),('barcode','=','WH-STOCK')],limit=1)
                rec.stock_picking_type_id.create({'name':'Stock Issue Voucher',
                                                  'sequence_id':ir_seq_obj.id,
                                                  'code':'internal',
                                                  'show_reserved':True,
                                                  'default_location_dest_id':stock_loc_src_obj.id,
                                                  'default_location_src_id':stock_loc_src_obj.id}) 
                rec.write({'stock_picking_type_id':self.env['stock.picking.type'].search([('name','=','Stock Issue Voucher')],limit=1).id})
            else:
                rec.write({'stock_picking_type_id':self.env['stock.picking.type'].search([('name','=','Stock Issue Voucher')],limit=1).id})
            stock_pick_obj=self.env['stock.picking']
#             proc_group_id=self.env['procurement.group']
#             stock_pick_obj.group_id.create({'name':rec.name,
#                                   'move_type':'direct',
#                                   'siv_id':rec.id})
#             proc_group_search_obj=self.env['procurement.group'].search([('siv_id','=',rec.id)],limit=1)
#             print('===================================group id:::::',proc_group_search_obj.name)
            uom_obj=self.env['uom.uom'].search([('name','=','Unit(s)')],limit=1)
            list_of_materials=[]
            for l in rec.siv_line_ids:
                list_of_materials.append([0,0,{'product_id':l.product_id.id,
                                               'product_uom_qty':l.initial_demand,
                                               'name':l.product_id.name,
                                               'location_id':rec.stock_picking_type_id.default_location_src_id.id,
                                               'location_dest_id':rec.stock_picking_type_id.default_location_dest_id.id,
                                               'procure_method':'make_to_stock',
                                               'product_uom':uom_obj.id
                                               }])
            stock_pick_obj.create({'location_id':rec.stock_picking_type_id.default_location_src_id.id,
                                   'location_dest_id':rec.stock_picking_type_id.default_location_dest_id.id,
                                   'picking_type_id':rec.stock_picking_type_id.id,
                                   'origin':rec.name,
                                   'priority':'1',
                                   'move_type':'direct',
#                                    'group_id':proc_group_search_obj.id,
                                   'move_ids_without_package':list_of_materials
                                   })
    @api.multi
    def production_move(self):
        """ Production internal transfer """
        for rec in self:
#             ir_seq_obj=self.env['ir.sequence'].search([('name','=','SSIV')],limit=1)
            stock_pick_obj=self.env['stock.picking']
            uom_obj=self.env['uom.uom'].search([('name','=','Unit(s)')],limit=1)
            list_of_materials=[]
            for l in rec.siv_line_ids:
                list_of_materials.append([0,0,{'product_id':l.product_id.id,
                                               'product_uom_qty':l.initial_demand,
                                               'name':l.product_id.name,
                                               'location_id':rec.stock_picking_type_id.default_location_dest_id.id,
                                               'location_dest_id':rec.location_id.id,
                                               'procure_method':'make_to_stock',
                                               'product_uom':uom_obj.id
                                               }])
            stock_pick_obj.create({'location_id':rec.stock_picking_type_id.default_location_dest_id.id,
                                   'location_dest_id':rec.location_id.id,
                                   'picking_type_id':rec.stock_picking_type_id.id,
                                   'origin':rec.name,
                                   'priority':'1',
                                   'move_type':'direct',
#                                    'group_id':proc_group_search_obj.id,
                                   'move_ids_without_package':list_of_materials
                                   })
            rec.write({'state':'prod_trans', 'stage':'prod_trans'})
                
    @api.multi  
    def call_internal_transfer(self):  
        mod_obj = self.env['ir.model.data']
        try:
            tree_res = mod_obj.get_object_reference('stock', 'vpicktree')[1]
            form_res = mod_obj.get_object_reference('stock', 'view_picking_form')[1]
        except ValueError:
            form_res = tree_res = False
        return {  
            'name': ('stock.picking'),  
            'type': 'ir.actions.act_window',  
            'view_type': 'form',  
            'view_mode': "[tree,form]",  
            'res_model': 'stock.picking',  
            'view_id': False,  
            'views': [(tree_res, 'tree'),(form_res, 'form')], 
            'domain': [('origin', '=', self.name)], 
            'target': 'current',  
               } 
                

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
    standard_price=fields.Float(string='Rate')
    amount=fields.Monetary(compute='_compute_amount')
    job_siv_id=fields.Many2one('job.siv')
    account_id=fields.Many2one('account.account', string='Expense Acct')
    account_contra_id=fields.Many2one('account.account', string='Contra Acct', related='product_id.categ_id.product_account_contra_categ_id')
    
    @api.onchange('product_id')
    def update_standard_price(self):
        for rec in self.filtered('product_id'):
            rec.standard_price = rec.product_id.standard_price
        
    
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
                
                
                
                
                
                
                
                
                
                
                
                
                
                
    
    
    
    
    
    
    
    
    
    
    
