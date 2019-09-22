# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JobSIV(models.Model):
    _name='job.siv'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description='SIV Related to Job'
    
    name=fields.Char('SIV No.')
    date=fields.Date(default=fields.Date.today())
    siv_job_id=fields.Many2one('manage.job',string='Job No.')
    job_description=fields.Char(string='Job Description', related='siv_job_id.description')
    siv_line_ids=fields.One2many('siv.line', 'job_siv_id')
    @api.model
    def create(self, values):
        res = super(JobSIV, self).create(values)
        for val in res:
            val['name'] = self.env['ir.sequence'].next_by_code('siv.seq')
        return res
    
class SIVLine(models.Model):
    _name="siv.line"
    _description="Lines of SIV Rec"
    
    product_id = fields.Many2one('product.product',string='Code', required=True)
    product_inte_ref=fields.Char(string='Description', related='product_id.default_code')
    quantity=fields.Integer()
    currency_id = fields.Many2one('res.currency', string="Currency", related='product_id.currency_id')
    standard_price=fields.Float(string='Rate', related='product_id.standard_price')
    amount=fields.Monetary(compute='_compute_amount')
    job_siv_id=fields.Many2one('job.siv')
    
    @api.depends('quantity','standard_price')
    def _compute_amount(self):
        for rec in self:
            rec.amount=rec.quantity*rec.standard_price
    
    
    
    