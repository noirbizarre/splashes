FROM docker.elastic.co/elasticsearch/elasticsearch:5.0.0

# Custom config:
#  - disable x-pack security
#  - cluster name
ADD elasticsearch.yml /usr/share/elasticsearch/config/

# Preinstall analysis-icu
RUN elasticsearch-plugin install analysis-icu
