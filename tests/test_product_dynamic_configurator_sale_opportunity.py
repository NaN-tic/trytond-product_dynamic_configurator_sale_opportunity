# This file is part product_dynamic_configurator_sale_opportunity module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest


from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite


class ProductDynamicConfiguratorSaleOpportunityTestCase(ModuleTestCase):
    'Test Product Dynamic Configurator Sale Opportunity module'
    module = 'product_dynamic_configurator_sale_opportunity'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            ProductDynamicConfiguratorSaleOpportunityTestCase))
    return suite
