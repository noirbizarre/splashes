import csv
import logging

from collections import Counter
from pathlib import Path

from .database import ES

log = logging.getLogger(__name__)

FILE_SUMMARY = '''
Summary:
🐣 Creations: %(creations)d
👥 Modifications: %(modifications)d
💀 Deletions: %(deletions)d
🤑 Commercial: %(commercial)d
💸 Non commercial: %(not_commercial)d
'''.strip()


class Loader(object):
    def __init__(self, config):
        self.config = config
        self.es = ES(config)

    def iter_csv(self, path, lines=None, progress=None, encoding='cp1252', delimiter=';'):
        with path.open(encoding=encoding) as csv_file:
            for i, data in enumerate(csv.DictReader(csv_file, delimiter=delimiter)):
                if i and progress and not i % progress:
                    log.info('%d lines loaded', i)

                if lines and i > lines:
                    break

                yield i, data

    def iter_insee_csv(self, path, lines=None, progress=None):
        return self.iter_csv(path, lines, progress)

    def iter_geo_csv(self, path, lines=None, progress=None):
        return self.iter_csv(path, lines, progress, encoding='utf-8', delimiter=',')

    def load(self, filename, lines=None, progress=None, geo=False):
        log.info('Loading stock data from  %s', filename)
        path = Path(filename)
        total = 0
        if path.is_dir():
            log.info('Loading data from %s directory', path)
            for i, file in enumerate(path.glob('*.csv')):
                total += self.process_stock_file(file, total, lines, progress, geo)
                log.debug('%d file processed', i)
        else:
            total += self.process_stock_file(path, total, lines, progress)
        log.info('%d items loaded with success', total)

    def process_stock_file(self, file, total, lines=None, progress=None, geo=False):
        log.info('Processing %s', file)
        processor = self.iter_geo_csv if geo else self.iter_insee_csv
        i = 0
        for i, data in processor(file, lines, progress):
            self.es.save_company(data)
        total += i
        log.info('%d items loaded with from file', i)
        return i

    def update(self, filename, lines=None, progress=None):
        path = Path(filename)
        counter = Counter({
            'creations': 0,
            'modifications': 0,
            'deletions': 0,
            'commercial': 0,
            'not_commercial': 0,
            'total': 0,
        })
        if path.is_dir():
            log.info('Loading updates from %s directory', path)
            for file in path.glob('*.csv'):
                self.process_update_file(file, counter, lines, progress)
        else:
            log.info('Loading updates from %s', path)
            self.process_update_file(path, counter, lines, progress)
        log.info('%(total)d items loaded with success', counter)

    def process_update_file(self, file, counter, lines=None, progress=None):
        log.info('Processing %s', file)
        for i, data in self.iter_insee_csv(file, lines, progress):
            vmaj = data['VMAJ']
            is_creation = vmaj == 'C'
            is_update_old = vmaj == 'I'
            is_update_new = vmaj == 'F'
            is_deletion = vmaj == 'E'
            is_commercial = vmaj == 'D'
            is_not_commercial = vmaj == 'O'

            if is_creation:
                counter['creations'] += 1
            elif is_update_old:
                # We remove one day from DATEMAJ to keep track of that state,
                # might be useful if company hasn't been loaded from stock.
                # TODO: really convert to a date! (or do not keep line?)
                data['DATEMAJ'] = str(int(data['DATEMAJ']) - 1)
            elif is_update_new:
                counter['modifications'] += 1
                # TODO: make sure that infos about the modif are propagated.
            elif is_deletion:
                counter['deletions'] += 1
                # TODO: make sure that infos about the deletion are propagated.
            elif is_commercial:
                counter['commercial'] += 1
            elif is_not_commercial:
                counter['not_commercial'] += 1
            else:
                log.error('Update type not supported: "%s"', vmaj)
                continue

            self.es.save_company(data)
        counter['total'] += i
        log.info(FILE_SUMMARY, counter)
