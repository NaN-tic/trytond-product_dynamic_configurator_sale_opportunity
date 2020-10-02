# This file is part product_dynamic_configurator_sale_opportunity module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import opportunity

def register():
    Pool.register(
        opportunity.Design,
        opportunity.QuotationLine,
        opportunity.SaleOpportunity,
        module='product_dynamic_configurator_sale_opportunity', type_='model')
