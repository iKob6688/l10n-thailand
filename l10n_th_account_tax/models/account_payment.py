# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    to_clear_tax = fields.Boolean(
        default=False,
        copy=False,
        help="When defer journal entry posting, this will show button",
    )
    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice",
        inverse_name="payment_id",
        copy=False,
        domain=[("reversing_id", "=", False), ("reversed_id", "=", False)],
    )
    tax_invoice_move_ids = fields.Many2many(
        comodel_name="account.move",
        relation="payment_tax_invoice_rel",
        column1="payment_id",
        column2="tax_invoice_id",
        string="Tax Invoice's Journal Entry",
        compute="_compute_tax_invoice_move_ids",
    )
    wht_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="payment_id",
        string="Withholding",
        copy=False,
        help="All withholding moves, including non-PIT",
    )
    pit_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="payment_id",
        string="Personal Income Tax",
        domain=[("is_pit", "=", True)],
        copy=False,
    )
    wht_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="payment_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )
    wht_certs_count = fields.Integer(
        string="# Withholding Tax Certs",
        compute="_compute_wht_certs_count",
    )

    @api.depends("wht_cert_ids")
    def _compute_wht_certs_count(self):
        for payment in self:
            payment.wht_certs_count = len(payment.wht_cert_ids)

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env.ref("l10n_th_account_tax.action_withholding_tax_cert_menu")
        result = action.sudo().read()[0]
        result["domain"] = [("id", "in", self.wht_cert_ids.ids)]
        return result

    def clear_tax_cash_basis(self):
        for payment in self:
            for tax_invoice in payment.tax_invoice_ids:
                if (
                    not tax_invoice.tax_invoice_number
                    or not tax_invoice.tax_invoice_date
                ):
                    raise UserError(_("Please fill in tax invoice and tax date"))
            payment.write({"to_clear_tax": False})
            moves = payment.tax_invoice_ids.mapped("move_id")
            for move in moves.filtered(lambda l: l.state == "draft"):
                move.ensure_one()
                move.action_post()
                # Reconcile Case Basis
                line = move.line_ids.filtered(
                    lambda l: l.id
                    not in payment.tax_invoice_ids.mapped("move_line_id").ids
                )
                if line.account_id.reconcile:
                    origin_ml = move.tax_cash_basis_origin_move_id.line_ids
                    counterpart_line = origin_ml.filtered(
                        lambda l: l.account_id.id == line.account_id.id
                    )
                    # Get counterpart line for expense
                    credit_move = move.tax_cash_basis_rec_id.credit_move_id
                    if hasattr(credit_move, "expense_id") and credit_move.expense_id:
                        counterpart_line = counterpart_line.filtered(
                            lambda l: l.expense_id.id == credit_move.expense_id.id
                        )
                    (line + counterpart_line).reconcile()
        return True

    @api.depends("tax_invoice_ids")
    def _compute_tax_invoice_move_ids(self):
        for payment in self:
            payment.tax_invoice_move_ids = payment.tax_invoice_ids.mapped("move_id")

    def button_journal_entries(self):
        moves = self.tax_invoice_move_ids + self.move_id
        return {
            "name": _("Journal Entries"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", moves.ids)],
        }

    def create_wht_cert(self):
        self.ensure_one()
        self.move_id.create_wht_cert()

    # The method _prepare_move_line_default_vals and its helper _update_line_vals_list
    # were heavily customized to inject WHT data into payment journal items.
    # In Odoo 18, _prepare_move_line_default_vals has been removed from account.payment.
    # The logic for creating payment move lines is now more centralized in the
    # account.payment.register wizard (for UI payments) or within _create_payment_vals
    # and related methods if payments are created programmatically.
    # This functionality will need to be re-implemented by targeting the appropriate
    # methods in account.payment.register or the new payment creation flow in account.payment.
    # For now, these outdated overrides are removed.
