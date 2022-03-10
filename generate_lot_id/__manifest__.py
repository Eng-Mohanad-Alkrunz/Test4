# -*- coding: utf-8 -*-
# © 2018 Mark Robinson, J3 Solution
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Generate Lot ID',
    'version': '15.0.0.0',
    'license': 'LGPL-3',
    'author': 'AHDTECH . ENG:Mohanad Alkrunz',
    'category': 'Inventory',
    'depends': ['product','mrp', 'product_expiry'],
    'data': [
        'views/product.xml',
        'reports/report_package_barcode.xml',
    ],
    'installable': True,
    'application': True,
}
