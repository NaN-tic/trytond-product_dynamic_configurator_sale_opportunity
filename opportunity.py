from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.modules.product import price_digits
from trytond.exceptions import UserError
from trytond.i18n import gettext

STATES = [
    ('quotation', 'Quotation'),
    ('confirmed', 'Confirmed'),
    ('rejected', 'Rejected'),
    ('cancel', 'Canceled'),
]

READONLY_STATE = {
    'readonly': (Eval('state') != 'draft'),
    }


class Design(metaclass=PoolMeta):
    __name__ = 'configurator.design'
    opportunity = fields.Many2One('sale.opportunity', 'Opportunity',
        domain=[If(Eval('party'), ('party', '=', Eval('party', -1)), ())],
        states=READONLY_STATE)

    @fields.depends('party', 'opportunity', '_parent_opportunity.party')
    def on_change_opportunity(self):
        self.party = self.opportunity and self.opportunity.party

    @classmethod
    def copy(cls, designs, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('opportunity', None)
        return super(Design, cls).copy(designs, default=default)

    @classmethod
    def process(cls, designs):
        super().process(designs)
        for design in designs:
            if not design.product:
                continue
            quotes = [line for line in design.prices if line.state == 'confirmed']
            if not quotes:
                continue
            quote = quotes[0]
            template = design.product.template
            template.list_price = quote.manual_list_price
            template.save()

    @classmethod
    def validate(cls, designs):
        for design in designs:
            design.check_quotation_confirmed()

    def check_quotation_confirmed(self):
        confirmed = [x for x in self.prices if x.state == 'confirmed']
        if confirmed and len(confirmed) > 1:
            raise UserError(gettext(
                'product_dynamic_configurator_sale_opportunity.msg_only_one_quotation_confirmed_allowed'))


class QuotationLine(metaclass=PoolMeta):
    __name__ = "configurator.quotation.line"

    state = fields.Selection(STATES, 'State', required=True,
        states={'readonly': Eval('design_state') != 'draft'})

    @staticmethod
    def default_state():
        return 'quotation'

    @classmethod
    def copy(cls, lines, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()

        default.setdefault('state', 'quotation')
        return super().copy(lines, default=default)


class SaleOpportunity(metaclass=PoolMeta):
    __name__ = "sale.opportunity"

    design = fields.One2Many('configurator.design', 'opportunity', 'Design')

    def get_rec_name(self, name):
        return "%s (%s) %s" % (self.number, self.reference, self.description)

    def get_quoted_lines(self, design, state=None):
        res = []
        for d in design:
            res += [line for line in d.prices if line.state in state]
        return res

    def get_design_sale_line(self, sale, quote_line):
        '''
        Return sale line for opportunity line
        '''
        SaleLine = Pool().get('sale.line')
        Uom = Pool().get('product.uom')

        if not quote_line.design.product:
            return

        sale_line = SaleLine(
            type='line',
            product=quote_line.design.product,
            sale=sale,
            description=None,
            )
        sale_line.on_change_product()
        sale_line.unit = quote_line.design.sale_uom
        quantity = Uom.compute_qty(quote_line.design.quotation_uom,
            quote_line.quantity, sale_line.unit, round=True)
        sale_line.quantity = quantity
        unit_price = quote_line.manual_list_price or quote_line.unit_price
        unit_price = Uom.compute_price(sale_line.product.default_uom,
            unit_price, sale_line.unit)
        sale_line.unit_price = round(unit_price, price_digits[1])
        return sale_line

    def create_sale(self):
        sale = super().create_sale()
        sale_lines = list(sale.lines) if sale.lines else []
        confirmed_lines = self.get_quoted_lines(self.design,
            'confirmed')

        for line in confirmed_lines:
            sale_line = self.get_design_sale_line(sale, line)
            if not sale_line:
                continue
            sale_lines.insert(0, sale_line)

        sale.lines = sale_lines
        return sale

    @classmethod
    def convert(cls, opportunities):
        Design = Pool().get('configurator.design')
        QuoteLine = Pool().get('configurator.quotation.line')

        designs = []
        rejected_lines = []
        for opportunity in opportunities:
            if not opportunity.design:
                continue
            designs += opportunity.design
            confirmed = opportunity.get_quoted_lines(opportunity.design,
                            'confirmed')
            if not confirmed:
                raise UserError(gettext(
                    'product_dynamic_configurator_sale_opportunity.msg_no_quotation_confirmed'))

            rejected_lines += opportunity.get_quoted_lines(opportunity.design,
                'quotation')

        QuoteLine.write(rejected_lines, {'state': 'rejected'})
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

        QuoteLine.write(rejected_lines, {'state': 'rejected'})
        Design.cancel(designs)

    @classmethod
    def cancel(cls, opportunities):
        super().cancel(opportunities)
        Design = Pool().get('configurator.design')
        QuoteLine = Pool().get('configurator.quotation.line')
        designs = []
        rejected_lines = []
        for opportunity in opportunities:
            designs += opportunity.design
            rejected_lines += opportunity.get_quoted_lines(opportunity.design,
                STATES)

        QuoteLine.write(rejected_lines, {'state': 'cancel'})
        Design.cancel(designs)

    @classmethod
    def copy(cls, opportunities, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('design', None)
        return super(SaleOpportunity, cls).copy(opportunities, default=default)
