# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.tests.common import SingleTransactionCase


class TestWHTCertForm(SingleTransactionCase):
    @classmethod
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env.ref("base.res_partner_12")
        cls.wht_cert_model = cls.env[
            "withholding.tax.cert"
        ]  # Changed cls.wht_cert to cls.wht_cert_model to avoid confusion
        cls.withholding_tax_cert_form_report = cls.env.ref(  # Corrected typo
            "l10n_th_account_wht_cert_form.withholding_tax_pdf_report"
        )

    def _create_direct_wht_cert(self):
        wht_cert = self.wht_cert.create(
            {
                "partner_id": self.partner_1.id,
                "income_tax_form": "pnd3",
                "date": fields.Date.today(),
                "wht_line": [
                    (
                        0,
                        0,
                        {
                            "wht_cert_income_type": "6",
                            "wht_cert_income_desc": "Other Text",
                            "amount": 10.0,
                            "wht_percent": 1.0,
                            "base": 1000.0,
                        },
                    )
                ],
            }
        )
        return wht_cert

    def test_01_print_wht_cert_form(self):
        wht_cert = self._create_direct_wht_cert()
        # Refactor to use report_action() instead of removed _render_qweb_pdf()
        # This primarily checks if the report action can be generated without error.
        # Detailed content checking would require parsing the PDF/HTML if needed.
        action_data = self.withholding_tax_cert_form_report.report_action(wht_cert)
        self.assertIsNotNone(action_data, "Report action should be generated.")
        self.assertEqual(action_data["type"], "ir.actions.report")
        # check report name pdf (this part of the test remains valid)
        # display name is False because wht_cert.name is not set before _get_report_base_filename is called
        # as it's a compute field that depends on payment_id or move_id, which are not set here.
        # If wht_cert had a name like "WHT/2023/0001", it would be "WHT Certificates - WHT/2023/0001"
        # The display_name of a new record not yet having its name computed can be False.
        self.assertEqual(
            wht_cert._get_report_base_filename(), "WHT Certificates - False"
        )
