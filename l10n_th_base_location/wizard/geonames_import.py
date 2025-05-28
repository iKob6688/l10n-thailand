# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import csv
import logging # Moved to top
import os

from odoo import api, fields, models
from odoo.modules.module import get_module_path # Moved to top

_logger = logging.getLogger(__name__) # Added logger instance


class CityZipGeonamesImport(models.TransientModel):
    _inherit = "city.zip.geonames.import"

    is_thailand = fields.Boolean(
        compute="_compute_is_thailand",
        help="For Thailand only, data is from TH_th.txt and TH_en.txt stored "
        "in the module's data folder. To get data from Geonames.org, "
        "please uninstall l10n_th_base_location.",
    )
    location_thailand_language = fields.Selection(
        [("th", "Thai"), ("en", "English")], string="Language of Thailand", default="th"
    )

    @api.depends("country_ids")
    def _compute_is_thailand(self):
        self.ensure_one()
        self.is_thailand = "TH" in self.country_ids.mapped("code")

    def _prepare_district_thailand(self, row):
        sub_district = ""
        district = ""
        if len(row) >= 6:
            district = row[5]
            if len(row) >= 7:
                sub_district = row[6]
        return district, sub_district

    @api.model
    def prepare_zip(self, row, city_id):
        vals = super().prepare_zip(row, city_id)
        district, sub_district = self._prepare_district_thailand(row)
        vals.update({"district_code": district, "sub_district_code": sub_district})
        return vals

    @api.model
    def select_zip(self, row, country, state_id):
        city_zip = super().select_zip(row, country, state_id)
        if country.code == "TH":
            # If District or Sub-District, update code
            district, sub_district = self._prepare_district_thailand(row)
            city_zip.write(
                {"district_code": district, "sub_district_code": sub_district}
            )
        return city_zip

    @api.model
    def get_and_parse_csv(self, country):
        if country.code == "TH":
            module_name = "l10n_th_base_location"
            module_path = get_module_path(module_name) # Uses import from top

            if not module_path:
                # Fallback or raise error if module path not found, though unlikely for self.
                return super().get_and_parse_csv(country)

            import_test = self._context.get("import_test", False)

            if import_test:
                data_subdir = "demo"
            else:
                data_subdir = "data"

            if self.location_thailand_language == "th":
                location_file_name = "TH_th.txt"
            else:
                location_file_name = "TH_en.txt"

            file_path = os.path.join(module_path, data_subdir, location_file_name)

            try:
                with open(file_path, "r", encoding="utf-8") as data_file:
                    # No need for data_file.seek(0) when reading fresh
                    reader = csv.reader(data_file, delimiter="\t")  # Original uses \t
                    parsed_csv = list(reader)  # Use list() as suggested by pylint
                return parsed_csv
            except FileNotFoundError:
                # Handle case where file might be missing, though it should be part of the module.
                # Log an error or fall back to super.
                # Let's log and fall back for robustness in case of packaging errors.
                _logger.error("Thai location file not found: %s", file_path) # Use %s formatting
                return super().get_and_parse_csv(country)

        return super().get_and_parse_csv(country)
