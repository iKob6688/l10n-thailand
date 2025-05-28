# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestFontSelection(TransactionCase):
    def test_thai_fonts_in_company_selection(self):
        """
        Test that Thai fonts added by l10n_th_fonts are available
        in res.company's 'font' field selection.
        """
        Company = self.env["res.company"]

        # Check if the 'font' field exists on res.company
        self.assertIn(
            "font",
            Company._fields,
            "The field 'font' does not exist on res.company model.",
        )

        # Get the selection options for the 'font' field
        font_selection = Company._fields["font"].selection

        # Convert the selection (list of tuples) to a dictionary for easier lookup
        # In Odoo 18, selection can also be a callable, handle that.
        if callable(font_selection):
            # If selection is a callable, it might need a model instance or env
            # For a static list like this, it's often directly inspectable or
            # we might need to call it with self.env.
            # For selection_add, it's usually directly modified.
            # However, the direct attribute _fields['field_name'].selection should give the list.
            # If it's a callable that depends on context, this test might need adjustment
            # or it implies a more dynamic selection than selection_add usually provides.
            # For now, we assume it's accessible as a list of tuples after selection_add.
            # This part might need refinement if selection_add behaves differently with callables in Odoo 18
            # than just appending to a static list.
            # For this basic test, we'll assume it resolves to a list of tuples.
            # A more robust way for callables might be:
            # font_selection_options = dict(Company.fields_get(allfields=['font'])['font']['selection'])
            # However, to directly test the effect of selection_add, inspecting _fields is more direct.
            pass # Keep font_selection as is if it's already a list

        font_selection_dict = dict(font_selection)

        # Fonts added by l10n_th_fonts
        expected_thai_fonts = [
            "THSrisakdi",
            "THSarabunNew",
            "THSarabun",
            "THNiramitAS",
            "THMaliGrade6",
            "THKrub",
            "THKoHo",
            "THKodchasal",
            "THK2DJuly8",
            "THFahkwang",
            "THCharmonman",
            "THCharmofAU",
            "THChakraPetch",
            "THBaijam",
            "AngsanaNew",
            # "Webdings" is also added, can be included if desired
        ]

        for font_key in expected_thai_fonts:
            self.assertIn(
                font_key,
                font_selection_dict,
                f"Font '{font_key}' not found in res.company font selection. "
                f"Available options: {list(font_selection_dict.keys())}",
            )

        # Optionally, check the label if needed, e.g.:
        # self.assertEqual(font_selection_dict["THSarabunNew"], "THSarabunNew")

        # Check a font that should NOT be there unless added by another module (as a negative check)
        # self.assertNotIn("NonExistentFont", font_selection_dict)
        # This negative check is usually not needed if we are only verifying additions.

        # Verify that the selection is not empty if it was empty before
        self.assertTrue(
            font_selection_dict, "Font selection on res.company should not be empty."
        )
