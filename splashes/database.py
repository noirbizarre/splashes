import logging

from datetime import datetime, date

from elasticsearch import Elasticsearch
from elasticsearch_dsl import analyzer, tokenizer, token_filter, Index as ESIndex


from elasticsearch_dsl import (
    DocType, Text, Keyword, Date, Boolean, Object, GeoPoint, Integer,
    analyzer, InnerObjectWrapper, Q
)


log = logging.getLogger(__name__)


# Deal with French specific aspects.
fr_stop_filter = token_filter('fr_stop_filter', type='stop', stopwords='_french_')

fr_stem_filter = token_filter('fr_stem_filter', type='stemmer', language='minimal_french')

fr_elision = token_filter(
    'fr_elision',
    type='elision',
    articles=[
        'l', 'm', 't', 'qu', 'n', 's', 'j', 'd', 'c',
        'jusqu', 'quoiqu', 'lorsqu', 'puisqu'
    ]
)

fr_analyzer = analyzer(
    'fr_analyzer',
    tokenizer=tokenizer('icu_tokenizer'),
    filter=['icu_folding', 'icu_normalizer', fr_elision, fr_stop_filter, fr_stem_filter],
    # char_filter=[char_filter('html_strip')]
)

simple = analyzer('simple')
standard = analyzer('standard')
filters = (fr_stop_filter, fr_stem_filter, fr_elision)


class Index(ESIndex):
    '''
    An Elasticsearch DSL index handling french filters and analyzers registeration.
    See: https://github.com/elastic/elasticsearch-dsl-py/issues/410
    '''
    def _get_mappings(self):
        mappings, _ = super(Index, self)._get_mappings()
        return mappings, {
            'analyzer': {fr_analyzer._name: fr_analyzer.get_definition()},
            'filter': {f._name: f.get_definition() for f in filters},
        }


#: Maps raw csv fields to document fields
MAPPING = {
    'siren': 'SIREN',
    'nic': 'NIC',
    'name': 'NOMEN_LONG',
    'headquarter': 'SIEGE',
    'sign': 'ENSEIGNE',
    'categorie': 'CATEGORIE',
    'legal': 'NJ',
    'ape': 'APEN700',
    'region': 'RPET',
    'departement': 'DEPET',
    'epci': 'EPCI',
    'workforce_block': 'TEFEN',
    'headquarter_region': 'RPEN',
    'shop_type': 'ACTISURF',
    'rna': 'RNA'
}

#: Maps raw csv fields to document date fields
DATE_MAPPING = {
    'activity_started': ('DDEBACT', '%Y%m%d'),
    'last_insee_update': ('DATEMAJ', '%Y%m%d'),
    'created_at_month': ('DCREN', '%Y%m'),
    'workforce_valid_at': ('DEFEN', '%Y'),
}

#: Maps raw csv fields to document boolean fields
BOOLEAN_MAPPING = {
    'seasonal': 'SAISONAT',
}

#: Maps raw csv fields to document integer fields
INTEGER_MAPPING = {
    'workforce': 'EFENCENT',
}

#: For response fields details see:
#: See https://www.elastic.co/guide/en/elasticsearch/reference/5.0/\
#:      docs-update-by-query.html#docs-update-by-query-response-body
DENORMALIZE_SUMMARY = '''
Summary:
✎ Updated: %(updated)d companies
⏱ Duration: %(took)d ms
'''.strip()


def parse_date(value, fmt):
    '''A failsafe date parser'''
    if not value:
        return None
    elif isinstance(value, (date, datetime)):
        return value
    try:
        return datetime.strptime(value, fmt).date()
    except Exception as e:
        log.exception('Unable to parse date "%s": %s', value, e)
        return None


def parse_boolean(value):
    '''a failsafe boolean parser'''
    # TODO: need implementation
    return value


def parse_int(value):
    '''a failsafe integer parser'''
    if not value or value == 'NN':
        return None
    elif isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception as e:
        log.exception('Unable to parse integer "%s": %s', value, e)
        return None


class Csv(InnerObjectWrapper):
    def get(self, name):
        '''Dict-like for easier extraction'''
        return getattr(self, name, None)


class Company(DocType):
    siret = Keyword()
    siren = Keyword()
    nic = Keyword()
    category = Keyword()
    legal = Keyword()
    ape = Keyword()
    region = Keyword()
    departement = Keyword()
    epci = Keyword()
    workforce = Integer()
    workforce_block = Keyword()
    headquarter_region = Keyword()
    shop_type = Keyword()
    rna = Keyword()

    seasonal = Keyword()

    # optionnal geolocation
    location = GeoPoint()

    name = Text(analyzer=fr_analyzer, fields={
        'raw': Keyword()
    })

    headquarter = Text(analyzer=fr_analyzer, fields={
        'raw': Keyword()
    })

    sign = Text(analyzer=fr_analyzer, fields={
        'raw': Keyword()
    })

    # Raw CSV values
    csv = Object(doc_class=Csv)

    # INSEE Tracking
    created_at_month = Date()
    activity_started = Date()
    last_insee_update = Date()
    workforce_valid_at = Date()

    # Local Tracking
    last_update = Date()

    def save(self, **kwargs):
        # Bulk map raw fields
        for key, field in MAPPING.items():
            setattr(self, key, self.csv.get(field))

        # Bulk map raw date fields
        for key, (field, fmt) in DATE_MAPPING.items():
            try:
                date = parse_date(self.csv.get(field), fmt)
            except ValueError:
                continue
            setattr(self, key, date)

        for key, field in INTEGER_MAPPING.items():
            try:
                value = parse_int(self.csv.get(field))
            except ValueError:
                continue
            setattr(self, key, value)

        # Bulk map raw boolean fields
        for key, field in BOOLEAN_MAPPING.items():
            try:
                value = parse_boolean(self.csv.get(field))
            except ValueError:
                continue
            setattr(self, key, value)

        # Set computed values
        self.meta.id = self.siret = self.siren + self.nic
        self.last_update = datetime.now()

        if self.csv.get('longitude') and self.csv.get('latitude'):
            self.location = '{0},{1}'.format(self.csv.latitude, self.csv.longitude)

        return super().save(**kwargs)


class ES(Elasticsearch):
    '''An elasticsearch connection manager/wrapper'''

    def __init__(self, config):
        super().__init__([config.elasticsearch])
        self.config = config
        index = Index(config.index, using=self)
        index.doc_type(Company)
        if not index.exists():
            index.create()

    def save_company(self, data):
        '''Save a company from its raw CSV data'''
        company = Company(csv=data)
        company.save(using=self)
        return company

    def get_company(self, siret):
        '''Get a company from its SIRET'''
        return Company.get(id=siret, using=self, index=self.config.index)

    def search_companies(self):
        '''Get a Search object for companies'''
        return Company.search(using=self, index=self.config.index)

    def denormalize(self, field, target_field, mapping, force=False):
        '''
        Perform denormalization on fields

        If you loaded data without labels, it allows to load them afterward.
        '''
        log.info('Denormalizing field %s into %s', field, target_field)
        if force:
            query = Q('match_all')
        else:
            query = ~Q('exists', field=target_field)
        body = {
            'query': query.to_dict(),
            'script': {
                'lang': 'painless',  # Default in ES5 but can be overriden by configuration
                'inline': 'ctx._source.csv[params.target] = params.mapping[ctx._source.csv[params.field]]',
                'params': {
                    'field': field,
                    'target': target_field,
                    'mapping': mapping,
                }
            },
        }
        # Compute timeout from count
        timeout = self.search_companies().query(query).count()
        result = self.update_by_query(
            index=self.config.index,
            doc_type=Company._doc_type.name,
            body=body,
            request_timeout=timeout
        )
        if result['failures']:
            log.error('Denormalization failed')
            for failure in result['failures']:
                log.error(failure)  # TODO: proper failure processing
        else:
            log.info(DENORMALIZE_SUMMARY, result)
