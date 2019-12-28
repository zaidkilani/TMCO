# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class ManageJob(models.Model):
    _name='manage.job'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='Job Management'
    
    name = fields.Char(readonly=True , string="Job Number")
    description=fields.Char()
    start_date = fields.Date(string='Start Date', default=fields.date.today())
    delivery_date = fields.Date(string='Delivery Date')
    sale_order_id=fields.Many2one('sale.order', string='Sale Order No.')
    analytic_account = fields.Many2one('account.analytic.account', string='Analytical Account')
    location_pro_id=fields.Many2one('stock.location', string='Production Location')
    state = fields.Selection([('new', 'New'), ('running', 'Running'),('onhold', 'On Hold'),('closed', 'Closed')], default="new")

    @api.multi
    def running(self):
        self.state="running"
    
    @api.multi
    def onhold(self):
        self.state="onhold"

    @api.multi
    def closed(self):
        self.state="closed"
    
    
    
    

   
    @api.model
    def create(self, values):
        res = super(ManageJob, self).create(values)
        for val in res:
            val['name'] = self.env['ir.sequence'].next_by_code('job.seq')
        for rec in res:
            if not rec.analytic_account:
                rec.ensure_one()
                rec.analytic_account.create({'name':rec.name})
                ana_acct_obj = rec.env['account.analytic.account'].search([('name','=',rec.name)])
                rec.write({'analytic_account':ana_acct_obj.id})
                rec.message_post(body="Analytic account has been added")
            else:
                raise UserError("This 'Job' is already assigned to an 'Analytic account'.")
            st_lo_obj=self.env['stock.location'].search([('name','=',rec.name)],limit=1)
            if st_lo_obj:
                rec.location_pro_id=st_lo_obj.id
            else:
                rec.location_pro_id.create({'name':rec.name,
                                            'usage':'production',
                                            'barcode':rec.name})
                rec.location_pro_id=self.env['stock.location'].search([('name','=',rec.name)],limit=1).id
        return res
    
    
    
    
    
    
