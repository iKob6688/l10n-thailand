# Copyright 2021 Sansiri Tanachutiwat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class CountryState(models.Model):
    _inherit = "res.country.state"

    def name_get(self):
        res = []
        th_states_names = {}  # Store names for TH states to preserve order later

        # Separate TH states from others
        other_states_ids = []
        for record in self:
            if record.country_id.code == "TH":
                th_states_names[record.id] = record.name
            else:
                other_states_ids.append(record.id)

        # Call super for non-TH states if any
        if other_states_ids:
            other_states = self.env["res.country.state"].browse(other_states_ids)
            super_res = super(CountryState, other_states).name_get()
            # Create a dictionary for easy lookup of super results
            super_res_dict = dict(super_res)
        else:
            super_res_dict = {}

        # Combine results, maintaining original order of self
        for record in self:
            if record.id in th_states_names:
                res.append((record.id, th_states_names[record.id]))
            elif record.id in super_res_dict:  # record.id should be in other_states_ids
                res.append((record.id, super_res_dict[record.id]))
            # else:
            # This case should ideally not happen if all records are processed.
            # Could add a fallback or error if necessary.
            # For now, assume all records fall into one of the categories.
        return res
