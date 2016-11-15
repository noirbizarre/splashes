# -*- coding: utf-8 -*-
import logging

import click

from .loader import Loader
from .utils import ObjectDict, is_tty


log = logging.getLogger(__name__)

CONTEXT_SETTINGS = {
    'help_option_names': ['-?', '-h', '--help']
}


def color(name, **kwargs):
    return lambda t: click.style(str(t), fg=name, **kwargs)

green = color('green', bold=True)
yellow = color('yellow', bold=True)
red = color('red', bold=True)
cyan = color('cyan')
magenta = color('magenta', bold=True)
white = color('white', bold=True)
bgred = color('white', bg='red')


OK = '✔'
KO = '✘'
WARNING = '⚠'


class ClickHandler(logging.Handler):
    '''Output using `click.echo`'''
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            err = level in ('warning', 'error', 'exception', 'critical')
            click.echo(msg, err=err)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class ClickFormatter(logging.Formatter):
    '''
    A log formatter using click ANSI colors and custom prefix when possible.
    '''
    LEVEL_COLORS = {
        'INFO': cyan,
        'WARNING': yellow,
        'ERROR': red,
        'CRITICAL': bgred,
        # 'DEBUG': bggrey
    }

    LEVEL_PREFIXES = {
        'INFO': cyan('ℹ'),
        'WARNING': yellow('⚠'),
        'ERROR': red('✘'),
        'CRITICAL': bgred('✘✘'),
    }

    def __init__(self, fmt=None, datefmt=None):
        fmt = fmt or '%(prefix)s %(message)s'
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format_multiline(self, value, color):
        value = value.replace('\n', '\n{0} '.format(color('│')))
        # replace last by a folding char
        value = '╰'.join(value.rsplit('│', 1))
        return value

    def format(self, record):
        '''Customize the line prefix and indent multiline logs'''
        level_color = self.LEVEL_COLORS.get(record.levelname, white)
        std_prefix = '{0}:'.format(record.levelname)
        prefix = self.LEVEL_PREFIXES.get(record.levelname, std_prefix) if is_tty() else std_prefix
        record.__dict__['prefix'] = level_color(prefix)
        record.msg = self.format_multiline(record.msg, level_color)
        return super().format(record)

    def formatException(self, ei):
        '''Indent traceback info for better readability'''
        out = super().formatException(ei)
        out = red('│') + self.format_multiline(out, red)
        return out


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-es', '--elasticsearch', help='Elasticsearch URL', default='http://localhost:9200')
@click.option('-i', '--index', help='Elasticsearch index name', default='sirene')
@click.pass_context
def cli(ctx, **kwargs):
    '''Elasticsearch loader for SIRENE dataset'''
    config = ctx.obj = ObjectDict(kwargs)

    log_level = logging.INFO if config.verbose else logging.WARNING

    handler = ClickHandler()
    handler.setLevel(log_level)
    handler.setFormatter(ClickFormatter())

    logger = logging.getLogger('splashes')
    logger.setLevel(log_level)
    logger.handlers = []
    logger.addHandler(handler)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-l', '--lines', type=int, help='Limit the amount of lines loaded')
@click.option('-p', '--progress', type=int, help='Show progress every X lines')
@click.option('-g', '--geo', is_flag=True, help='Process the geo-sirene files')
@click.pass_obj
def load(config, path, lines=None, progress=None, geo=False):
    '''Load data from a stock CSV file(s)'''
    loader = Loader(config)
    loader.load(path, lines=lines, progress=progress, geo=geo)
    click.echo(green(OK) + white(' Done'))


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-l', '--lines', type=int, help='Limit the amount of lines loaded')
@click.option('-p', '--progress', type=int, help='Show progress every X lines')
@click.pass_obj
def update(config, path, lines=None, progress=None):
    '''Load updates from daily generated CSV files'''
    loader = Loader(config)
    loader.update(path, lines=lines, progress=progress)
    click.echo(green(OK) + white(' Done'))


@cli.command()
@click.pass_obj
def info(config):
    '''Display configuration and data statistics'''
    click.echo(cyan('SplashES configuration'))
    for key, value in config.items():
        click.echo('{0}: {1}'.format(white(key), value))


@cli.command()
@click.pass_obj
def shell(config):
    '''Launch an interactive sheel (requires iPython)'''
    try:
        from IPython import embed
    except ImportError:
        log.error('This command requires ipython')
    from .database import ES, Company  # noqa: F401
    es = ES(config)  # noqa: F841
    embed()


def main():
    '''
    Start the cli interface.
    This function is called from the entrypoint script installed by setuptools.
    '''
    cli(obj={}, auto_envvar_prefix='SPLASHES')


# Allow running this file as standalone app without setuptools wrappers
if __name__ == '__main__':
    main()
