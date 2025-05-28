# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    tax_invoice_number = fields.Char(copy=False)
    tax_invoice_date = fields.Date(copy=False)

    def reverse_moves(self):
        self.ensure_one()
        # Send context to reverse moves for case Full Refund
        # because it will auto post moves
        if self.move_type == "in_invoice":
            self = self.with_context(
                tax_invoice_number=self.tax_invoice_number,
                tax_invoice_date=self.tax_invoice_date,
            )
        action = super().reverse_moves()

        # After super, potentially update tax invoice details on the created reversal move(s)
        # This is mainly for cases where the reversal is not posted directly by super()
        # or if the _post() method didn't pick up the context for some reason.
        if (
            self.move_type == "in_invoice"
            and self.tax_invoice_number
            and self.tax_invoice_date
        ):
            new_move_ids = []
            if action.get("res_id"):
                new_move_ids.append(action["res_id"])
            elif action.get("res_ids") and isinstance(action.get("res_ids"), list):
                new_move_ids.extend(action.get("res_ids"))
            elif action.get("domain") and isinstance(action.get("domain"), list):
                for term in action.get("domain"):
                    if isinstance(term, (list, tuple)) and term[0] == "id":
                        if term[1] == "=" and isinstance(term[2], int):
                            new_move_ids.append(term[2])
                        elif term[1] == "in" and isinstance(term[2], list):
                            new_move_ids.extend(term[2])

            if new_move_ids:
                reversed_moves = self.env["account.move"].browse(new_move_ids)
                for move_reversal in reversed_moves:
                    # Target relevant purchase tax lines on the reversal
                    purchase_tax_invoices = move_reversal.tax_invoice_ids.filtered(
                        lambda ti: ti.tax_line_id.type_tax_use == "purchase"
                        or (
                            move_reversal.move_type == "entry"
                            and not ti.payment_id
                            and move_reversal.journal_id.type != "sale"
                            and ti.tax_line_id.type_tax_use != "sale"
                        )
                    )
                    # Update only if not already set (e.g., by _post if move was posted)
                    if purchase_tax_invoices and not any(
                        purchase_tax_invoices.mapped("tax_invoice_number")
                    ):
                        purchase_tax_invoices.write(
                            {
                                "tax_invoice_number": self.tax_invoice_number,
                                "tax_invoice_date": self.tax_invoice_date,
                            }
                        )
        return action
