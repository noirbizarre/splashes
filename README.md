# SplashES

Elasticsearch loader and playground for SIRENE dataset

## Requirements

This project is meant to be run with [Docker][] so it requires:

- A Unix-compatible environment (Linux, MacOSX)
- [Docker][] et [Docker Compose][]

You can also run it the native way, in this case the requirements are:

- [Elasticsearch][] 5.0
- Python 3.5

In both case, Elasticsearch 5.0 requires to run:

```shell
# As root
sysctl -w vm.max_map_count=262144
# As user with permissions
sudo sysctl -w vm.max_map_count=262144
```

More details in the [Elasticsearch Virtual Memory documentation section][es-vm-doc]
and the [officiel docker details][es-docker-vm-doc]


## Getting started

For quick start, splashes provides a dockerized playground which
we will use to get ready.

You can use it in three ways:

1. **Fully native:** native `splashes` on Python 3.5 with native Elasticsearch 5.0
2. **Hybrid:** native `splashes` on Python 3.5 with dockerized Elasticsearch/Kibana
3. **Fully dockerized:** fully dockerized environment

### Fully native

Install [Elasticsearch][] using your favorite package manager or
as described [on the official documentation][es-install].

Then, install the [ICU Analysis Plugin][] using the elasticsearch plugin manager:

```
$ELASTIC_HOME/bin/elasticsearch-plugin install analysis-icu
```
*(where `$ELASTIC_HOME` is the Elasticsearch installation directory)*

Restart Elasticsearch and you can then install the python executable with:

```shell
pip install -e .
splashes --help
```

### Hybrid

In this configuration, you will use the provided [Elasticsearch][]/[Kibana][] docker stack
with [Docker Compose][].
A `./dc` executable helper is provided to manipulate `docker-compose`.
Persistent data are stored into the `elasticsearch/data` directory.

Start the Elastcisearch stack with
```shell
./dc up
```
Then go grab a coffee because it can take some times on the first launch.

This command use your current terminal, so if you want to launch everything in the background
execute this command instead:

```shell
./dc up -d
```

You can then access:

- elasticsearch on <http://localhost:9200>
- kibana on <http://localhost:5601>

Then install the `splashes` application:

```shell
pip install -e .
splashes --help
```

**Note:** You can override docker-compose configuration with a `docker-compose.override.yml` file.

### Fully dockerized

This methods use the provided [Elasticsearch][]/[Kibana][] docker stack from the hybrid method
plus a dockerized `splashes` application.
You will use the `./dc-splashes` helper to manipulate both `docker-compose` and `splashes`.

You can download and/or build docker images and get the services up and ready with:

```shell
./dc-splashes up
```

This command use your current terminal, so if you want to launch everything in the background
execute this command instead:

```shell
./dc-splashes up -d
```

You can then access:

- elasticsearch on <http://localhost:9200>
- kibana on <http://localhost:5601>

and you can use `splashes` with:

```shell
./dc-splashes --help
```

**Note:** You can override docker-compose configuration with a `docker-compose.override.yml` file.


## Commands

You can list all available commands using:

```shell
splashes --help
```

You can have help on each command using:

```shell
splashes CMD --help
```

You can pass common options before your command:

```shell
splashes --es http://elastic.somewhere.com --index splahes -v CMD
```

Options are:

* **-es**/**--elasticsearch**: The Elasticsearch URL, defaults to <http://localhost:9200>
* **-i**/**--index**: The Elasticsearch index, defaults to `sirene`
* **-v**/**--verbose**: More verbose output

You can also use environment variables:

* `SPLASHES_ELASTICSEARCH`
* `SPLASHES_INDEX`
* `SPLASHES_VERBOSE`


### Loading data

You can load stock data with:

```shell
splashes load my-data.csv
```

and daily updates with:

```shell
splashes update daily/updates/directory
# or
splashes update daily/updates/directory/file.csv
```

both commands accept to optionnal parameters:

* `-l`/`--lines` to limit the amount of data loaded to X lines
* `-p`/`--progress` to display progression indication every X lines

**Note:** the fully dockerized methods requires the dataset to be present in the current directory
(or any child directory) or to add the directory as a volume.

The `load` can also load [geo-sirene][] data with the `--geo` parameter:

```shell
splashes load path/to/geo-sirene/data --geo -l 100000 -p 1000
```

### Interactive shell

This feature requires [IPython][]

```shell
pip install ipython
splashes --es http://my.elasticsearch:9200 shell
```

You will land in IPython interactive shell with the following objects available:

* `es`: an instaciated Elasticsearch connection
* `Company`: the elasticsearch documents model class
* `config`: the global `splashes` configuration

```IPython
# List PME names
companies = es.search_companies().filter(legal='SARL', category='PME').execute()
for company in companies:
    print(company.name)
```

The `search_companies()` methods returns a [Search object][]
See the [Elasticsearch DSL][] documentation


## Elasticsearch and kibana plugins with docker

You can install extra elasticsearch plugins with:

```shell
./dc run elasticsearch elasticsearch-plugin install my-plugin
```

Don't forget to restart elasticsearch by either using `CTRL-C` if docker-compose is on the foreground
or `docker-compose stop && docker-compose up -d` when running in the background.

You can install extra Kibana plugins with:

```shell
./dc run kibana kibana-plugin install my-plugin
```

[Docker]: https://www.docker.com/
[Docker Compose]: https://docs.docker.com/compose/
[Elasticsearch]: https://www.elastic.co/products/elasticsearch
[Kibana]: https://www.elastic.co/products/kibana
[es-vm-doc]: https://www.elastic.co/guide/en/elasticsearch/reference/5.0/vm-max-map-count.html
[es-docker-vm-doc]: https://github.com/elastic/elasticsearch-docker#user-content-host-prerequisites
[es-install]: https://www.elastic.co/guide/en/elasticsearch/reference/5.0/install-elasticsearch.html
[ICU Analysis Plugin]: https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html
[IPython]: https://ipython.org/
[Elasticsearch DSL]: https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html
[Search object]: https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html#the-search-object
[geo-sirene]: https://github.com/cquest/geocodage-sirene
