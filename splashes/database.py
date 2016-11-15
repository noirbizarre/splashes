import logging

from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch_dsl import analyzer, tokenizer, token_filter, Index as ESIndex


from elasticsearch_dsl import DocType, Text, Keyword, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Object, GeoPoint, Integer


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
    'categorie': 'CATEGORIE',
    'legal': 'NJ',
    'ape': 'APEN700',
    'region': 'RPET',
    'departement': 'DEPET',
    'workforce': 'EFENCENT',
    'workforce_block': 'TEFEN',
}

#: Maps raw csv date fields to document fields
DATE_MAPPING = {
    'activity_started': ('DDEBACT', '%Y%m%d'),
    'last_insee_update': ('DATEMAJ', '%Y%m%d'),
    'created_at_month': ('DCREN', '%Y%m'),
    'workforce_valid_at': ('DEFEN', '%Y'),
}


def parse_date(value, fmt):
    '''A failsafe date parser'''
    if not value:
        return None
    try:
        return datetime.strptime(value, fmt).date()
    except Exception as e:
        log.exception('Unable to parse date "%s": %s', value, e)
        return None


class Company(DocType):
    siret = Keyword()
    siren = Keyword()
    nic = Keyword()
    category = Keyword()
    legal = Keyword()
    ape = Keyword()
    region = Keyword()
    departement = Keyword()
    workforce = Integer()
    workforce_block = Keyword()
    location = GeoPoint()

    name = Text(analyzer=fr_analyzer, fields={
        'raw': Keyword()
    })

    # Raw CSV values
    csv = Object()

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
            setattr(self, key, getattr(self.csv, field, None))

        # Bulk map raw date fields
        for key, (field, fmt) in DATE_MAPPING.items():
            try:
                date = parse_date(getattr(self.csv, field, None), fmt)
            except ValueError:
                continue
            setattr(self, key, date)

        # Set computed values
        self.meta.id = self.siret = self.siren + self.nic
        self.last_update = datetime.now()

        if getattr(self.csv, 'longitude', None) and getattr(self.csv, 'latitude', None):
            self.location = {
                'lat': self.csv.latitude,
                'lon': self.csv.longitude
            }

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
        company = Company(csv=data)
        company.save(using=self)
        return company

    def get_company(self, siret):
        return Company.get(id=siret, using=self, index=self.config.index)

    def search_companies(self):
        return Company.search(using=self, index=self.config.index)
