from trytond.model import ModelView, ModelSQL, fields, sequence_ordered, tree
from trytond.pool import Pool, PoolMeta

STATES = [
    ('quotation', 'Quotation'),
    ('confirmed', 'Confirmed'),
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

    design = fields.One2Many('configurator.design', 'opportunity', 'Design')

    def get_quoted_lines(self, design, state = None):
        res = []
        for d in design:
            res += [line for line in d.prices if line.state in state]
        return res

    def get_design_sale_line(self, sale, quote_line):
        '''
        Return sale line for opportunity line
        '''
        SaleLine = Pool().get('sale.line')
        sale_line = SaleLine(
            type='line',
            product=quote_line.design.product,
            sale=sale,
            description=None,
            )
        sale_line.on_change_product()
        self._set_design_sale_line_quantity(sale_line, quote_line)
        return sale_line

    def _set_design_sale_line_quantity(self, sale_line, quote_line):
        sale_line.quantity = quote_line.quantity
        sale_line.unit = quote_line.uom
        sale_line.unit_price = quote_line.unit_price


    def create_sale(self):
        sale = super().create_sale()
        sale_lines = list(sale.lines) if sale.lines else []
        confirmed_lines = self.get_quoted_lines(self.design,
            'confirmed')
        for line in confirmed_lines:
            sale_lines.append(self.get_design_sale_line(sale, line))

        sale.lines = sale_lines
        return sale

    @classmethod
    def convert(cls, opportunities):
        Design = Pool().get('configurator.design')
        QuoteLine = Pool().get('configurator.quotation.line')

        designs = []
        rejected_lines = []
        for opportunity in opportunities:
            designs += opportunity.design
            rejected_lines += opportunity.get_quoted_lines(opportunity.design,
                'quotation')

        QuoteLine.write(rejected_lines, {'state':'rejected'})
        Design.process(designs)

        super().convert(opportunities)

    @classmethod
    def lost(cls, opportunities):
        super().lost(opportunities)
        Design = Pool().get('configurator.design')
        QuoteLine = Pool().get('configurator.quotation.line')
        designs = []
        rejected_lines = []
        for opportunity in opportunities:
            designs += opportunity.design
            rejected_lines += opportunity.get_quoted_lines(opportunity.design,
                STATES)

        QuoteLine.write(rejected_lines, {'state':'rejected'})
        Design.cancel(designs)

    @classmethod
    def cancel(cls, opportunities):
        super().lost(opportunities)
        Design = Pool().get('configurator.design')
        QuoteLine = Pool().get('configurator.quotation.line')
        designs = []
        rejected_lines = []
        for opportunity in opportunities:
            designs += opportunity.design
            rejected_lines += opportunity.get_quoted_lines(opportunity.design,
                STATES)

        QuoteLine.write(rejected_lines, {'state':'cancel'})
        Design.cancel(designs)

    @classmethod
    def copy(cls, opportunities, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('design', None)
        return super(SaleOpportunity, cls).copy(opportunities, default=default)
