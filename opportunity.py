from trytond.model import ModelView, ModelSQL, fields, sequence_ordered, tree
from trytond.pool import Pool, PoolMeta

STATES = [
    ('quotation', 'Quotation'),
    ('confirmed', 'Confirmed'),
    ('done', 'Done'),
    ('rejected', 'Rejected'),
    ('cancel', 'Canceled'),
]


class Design(metaclass=PoolMeta):
    __name__ = 'configurator.design'
    party = fields.Many2One('party.party', 'Party')
    opportunity = fields.Many2One('sale.opportunity', 'Oportunity')


class QuotationLine(metaclass=PoolMeta):
    __name__ = "configurator.quotation.line"

    state = fields.Selection(STATES, 'State', readonly=False, required=True)

    @staticmethod
    def default_state():
        return 'quotation'


class SaleOpportunity(metaclass=PoolMeta):
    __name__ = "sale.opportunity"

    design = fields.One2Many('configurator.design', 'opportunity', 'Design', size=1)

    # configurator_quote = fields.One2Many('configurator.quotation.line', 'opportunity', 'Opportunity')
