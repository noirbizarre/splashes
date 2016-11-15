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

More details in the [Elasticsearch Virtual Memory documentation section][vm-doc]
and the [officiel docker details][es-docker-vm-doc]


## Getting started

For quick start, splashes provides a dockerized playground which
we will use to get ready.

You can use it in three ways:
1. native Python 3.5 with native Elasticsearch 5.0
2. native Python 3.5 with dockerized Elasticsearch/Kibana
3. fully dockerized environment

With **1** and **2**, you will install and use the `splashes` executable on host.
With **2**, you will use the `./dc-splashes` helper.

For **2** and **3**, you can user the `./dc` helper for manipulating `docker-compose`.
Persistent data are stored into the `elasticsearch/data` directory.

You can override docker-compose configuration with a `docker-compose.override.yml` file.


### Docker dependencies

The following command will pull required docker images, build the splashes docker image
and launch all services to get ready:

```shell
./dc up
```
Then go grab a coffee because it can take some times on the first launch.

This command use your current terminal, so if you want to launch everythin in the background
execute this command instead:

```shell
./dc up -d
```

You can then access:

- elasticsearch on <http://localhost:9200>
- kibana on <http://localhost:5601>

### Loading data

As we are using elastic search, we need to get the files available into the current directory.

```shell
splashes load my-data.csv
```


### Commands

You can list all available commands using:

```shell
splashes --help
```

You can have help on each command using:

```shell
splashes CMD --help
```

## Elasticsearch and kibana plugins

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

## Native usage

If you don't want to use Docker, you can use `splashes` like yo would for any python command line client.

```shell
pip install -e .
splashes --help
```

By default, `splashes` expect Elasticsearch to be running on <http://localhost:9200>
But you can specify another location with the `--es` parameter:

```shell
splashes --es http://somwhere.com:9200/ load myfile.csv
```


[Docker]: https://www.docker.com/
[Docker Compose]: https://docs.docker.com/compose/
[Elasticsearch]: https://www.elastic.co/
[vm-doc]: https://www.elastic.co/guide/en/elasticsearch/reference/5.0/vm-max-map-count.html
[es-docker-vm-doc]: https://github.com/elastic/elasticsearch-docker#user-content-host-prerequisites
