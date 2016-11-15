from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch_dsl import analyzer, tokenizer, token_filter, Index as ESIndex


from elasticsearch_dsl import DocType, Text, Keyword, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Object, GeoPoint


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

class Company(DocType):
    siret = Keyword()
    siren = Keyword()
    nic = Keyword()
    region = Keyword()
    departement = Keyword()
    location = GeoPoint()

    name = Text(analyzer=fr_analyzer, fields={
        'raw': Keyword()
    })

    # Raw CSV values
    csv = Object()

    # Tracking
    last_update = Date()

    def save(self, **kwargs):
        self.siret = self.siren + self.nic
        self.last_update = datetime.now()

        if self.csv.get('longitude') and self.csv.get('latitude'):
            self.location = {
                'lat': self.csv['latitude'],
                'lon': self.csv['longitude']
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

    def save(self, company):
        company.save(using=self)
        return company
