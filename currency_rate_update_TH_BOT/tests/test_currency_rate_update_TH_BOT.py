# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestResCurrencyRateProviderBOT(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Company = cls.env["res.company"]
        cls.CurrencyRate = cls.env["res.currency.rate"]
        cls.CurrencyRateProvider = cls.env["res.currency.rate.provider"]

        cls.today = fields.Date.today()
        cls.thb_currency = cls.env.ref("base.THB")
        cls.eur_currency = cls.env.ref("base.EUR")
        cls.my_company = cls.Company.create(
            {"name": "Test Company", "currency_id": cls.thb_currency.id}
        )
        cls.none_provider = cls.CurrencyRateProvider.create(
            {
                "service": "none",
                "currency_ids": [(4, cls.eur_currency.id)],
                "company_id": cls.my_company.id,
            }
        )
        cls.bot_provider = cls.CurrencyRateProvider.create(
            {
                "service": "BOT",
                "currency_ids": [(4, cls.eur_currency.id)],
                "company_id": cls.my_company.id,
            }
        )
        cls.CurrencyRate.search([]).unlink()

    def test_01_supported_currencies(self):
        # None
        supported_currencies = self.none_provider._get_supported_currencies()
        self.assertNotEqual(len(supported_currencies), 48)
        # BOT
        supported_currencies = self.bot_provider._get_supported_currencies()
        self.assertEqual(len(supported_currencies), 48)

    def test_02_base_curency_not_THB(self):
        self.company1 = self.Company.create(
            {"name": "Test Company EUR", "currency_id": self.eur_currency.id}
        )
        self.bot_provider1 = self.CurrencyRateProvider.create(
            {
                "service": "BOT",
                "currency_ids": [(4, self.thb_currency.id)],
                "company_id": self.company1.id,
            }
        )
        date = self.today - relativedelta(days=1)
        with self.assertRaisesRegex(
            UserError,
            "Bank of Thailand is suitable only for companies with THB as base currency!",
        ):
            self.bot_provider1._update(date, date)
        # Check service BOT
        self.assertIn(self.eur_currency, self.bot_provider1.available_currency_ids)
        # Ensure that none_provider update still works (no error)
        self.none_provider._update(date, date)

    @patch(
        "odoo.addons.currency_rate_update_TH_BOT.models.res_currency_rate_provider_BOT.requests.get"
    )
    def test_03_update_no_client_id(self, mock_get):
        self.my_company.bot_client_id = False
        date = self.today - relativedelta(days=1)
        with self.assertRaisesRegex(UserError, "No bot.or.th credentials specified!"):
            self.bot_provider._update(date, date)
        mock_get.assert_not_called()

    @patch(
        "odoo.addons.currency_rate_update_TH_BOT.models.res_currency_rate_provider_BOT.requests.get"
    )
    def test_04_update_client_id_api_error_handling(self, mock_get):
        self.my_company.bot_client_id = "Test"
        date = self.today - relativedelta(days=1)

        # Scenario 1: API returns an error structure
        mock_get.return_value.ok = False  # Simulate HTTP error
        mock_get.return_value.json.return_value = {
            # "result": False, # This key might be missing in some error responses
            "httpCode": "401",
            "moreInformation": "Unauthorized - Invalid API Key",
        }
        with self.assertRaisesRegex(
            UserError, "httpCode: 401\nmoreInformation: Unauthorized - Invalid API Key"
        ):
            self.bot_provider._update(date, date)
        mock_get.assert_called_once()

        # Scenario 2: API returns success (ok=True) but 'result' key is missing or False
        mock_get.reset_mock()
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            "httpCode": "200",  # Present but no 'result'
            "moreInformation": "Success but no result field",
        }
        with self.assertRaisesRegex(
            UserError, "httpCode: 200\nmoreInformation: Success but no result field"
        ):
            self.bot_provider._update(date, date)
        self.assertEqual(mock_get.call_count, 1)

        # Scenario 3: API returns success, 'result' is present, but 'data_detail' is empty
        mock_get.reset_mock()
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {
            "result": {
                "data_header": {"last_updated": date.strftime("%Y-%m-%d")},
                "data_detail": [],  # No currency data for the requested period/currency
            }
        }
        # This should not raise an error, but simply find no rates
        self.bot_provider._update(date, date)
        rates = self.CurrencyRate.search(
            [
                ("company_id", "=", self.my_company.id),
                ("currency_id", "=", self.eur_currency.id),
                ("name", "=", date),
            ]
        )
        self.assertEqual(len(rates), 0)
        self.assertEqual(mock_get.call_count, 1)  # Called for EUR

    def test_05_update_content(self):
        """After call api to BOT, it will return value"""
        result_demo = {
            "timestamp": "2023-09-19 00:00:00",
            "api": "Daily Weighted-average Interbank Exchange Rate - THB / USD",
            "data": {
                "data_header": {
                    "report_name_eng": "Rates of Exchange of Commercial Banks in "
                    "Bangkok Metropolis (2002-present)",
                    "report_name_th": "อัตราแลกเปลี่ยนเฉลี่ยของธนาคารพาณิชย์"
                    "ในกรุงเทพมหานคร (2545-ปัจจุบัน)",
                    "report_uoq_name_eng": "(Unit: Baht / 1 Unit of Foreign Currency)",
                    "report_uoq_name_th": "(หน่วย: บาท ต่อ 1 หน่วยเงินตราต่างประเทศ)",
                    "report_source_of_data": [
                        {
                            "source_of_data_eng": "Bank of Thailand",
                            "source_of_data_th": "ธนาคารแห่งประเทศไทย",
                        }
                    ],
                    "report_remark": [
                        {
                            "report_remark_eng": "Since Nov 16, 2015 the data regarding "
                            "Buying Transfer Rate of PKR has been changed to "
                            "Buying Rate using Foreign Exchange Rates "
                            "(THOMSON REUTERS) with Bangkok Market Crossing.",
                            "report_remark_th": "ตั้งแต่วันที่ 16 พ.ย. 2558 "
                            "ข้อมูลในอัตราซื้อเงินโอนของสกุล PKR ได้เปลี่ยนเป็นอัตราซื้อ"
                            "ที่ใช้อัตราในตลาดต่างประเทศ (ทอมสันรอยเตอร์) คำนวณ"
                            "ผ่านอัตราซื้อขายเงินดอลลาร์ สรอ. ในตลาดกรุงเทพฯ",
                        }
                    ],
                    "last_updated": "2023-09-19",
                },
                "data_detail": [
                    {
                        "period": "2023-09-19",
                        "currency_id": "USD",
                        "currency_name_th": "สหรัฐอเมริกา : ดอลลาร์ (USD)",
                        "currency_name_eng": "USA : DOLLAR (USD) ",
                        "buying_sight": "35.5795000",
                        "buying_transfer": "35.6563000",
                        "selling": "35.9808000",
                        "mid_rate": "35.8186000",
                    }
                ],
            },
        }
        date = datetime.datetime.strptime("2023-09-19", "%Y-%m-%d").date()
        # Test with content there is no value
        self.bot_provider._update_content_currency_update(
            self.eur_currency, {}, result_demo, date, date
        )
        # Test with content there is value
        self.bot_provider._update_content_currency_update(
            self.eur_currency,
            {"2023-09-19": {"USD": 0.027918455774374205}},
            result_demo,
            date,
            date,
        )
        # Check not found currency when call api (date_from > last_updated)
        with self.assertRaisesRegex(UserError, "BOT Last Updated: 2023-09-10"):
            result_demo_error = result_demo.copy()
            result_demo_error["data"] = result_demo["data"].copy()
            result_demo_error["data"]["data_header"] = result_demo["data"][
                "data_header"
            ].copy()
            result_demo_error["data"]["data_header"]["last_updated"] = "2023-09-10"
            # date is 2023-09-19, so date > last_updated
            self.bot_provider._update_content_currency_update(
                self.eur_currency, {}, result_demo_error, date, date
            )
