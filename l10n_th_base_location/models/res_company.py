# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _inverse_street2(self):
        return super(
            ResCompany, self.with_context(skip_check_zip=True)
        )._inverse_street2()

    @api.onchange("zip_id")
    def _onchange_zip_id(self):
        res = super()._onchange_zip_id()
        # Ensure city_id and its name exist before splitting
        if (
            self.zip_id
            and self.country_id.code == "TH"
            and self.zip_id.city_id
            and self.zip_id.city_id.name
        ):
            address_parts = self.zip_id.city_id.name.split(
                ", ", 1
            )  # Split at most once
            if len(address_parts) == 2:
                self.street2 = address_parts[0]
                self.city = address_parts[1]
            # If city_id.name doesn't contain ", ", address_parts will have 1 element.
            # In this case, the original code would error on address[1]. This revised version
            # will only update if two parts are found.
            # Alternative: if len(address_parts) == 1, assign address_parts[0] to self.city or 
            # self.street2. However, sticking to the original intent of splitting "District, City" 
            # seems more appropriate.
        return res
