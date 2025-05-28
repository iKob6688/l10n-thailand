# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    customer_tax_name = fields.Selection(
        [
            ("payment", "Payment"),
            ("invoice", "Invoice"),
        ],
        default="payment",
        string="Customer Tax Invoices Number",
        help="Determines whether the customer tax invoice number should be based on the payment's name or the invoice's name/reference.",
    )
