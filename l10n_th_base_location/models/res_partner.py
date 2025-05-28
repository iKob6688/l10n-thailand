# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("zip_id", "country_id")  # Added country_id to depends
    def _compute_city(self):
        super()._compute_city()  # Let super do its work first
        for record in self.filtered(
            lambda r: r.zip_id
            and r.country_id.code == "TH"
            and r.zip_id.city_id
            and r.zip_id.city_id.name
        ):
            address_parts = record.zip_id.city_id.name.split(
                ", ", 1
            )  # Split at most once
            if len(address_parts) == 2:
                record.street2 = address_parts[0]
                record.city = address_parts[1]
            # If city_id.name doesn't contain ", ", address_parts will have 1 element.
            # The original code would error. This revised version only updates if two parts 
            # are found. Consider alternative handling if only one part (e.g., assign to record.city).
            # For now, this matches the safe update pattern from res_company.
        # Compute methods typically do not return a value; they modify 'self'.
