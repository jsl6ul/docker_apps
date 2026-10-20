FROM netboxcommunity/netbox:{{ dapp_netbox_version }}
COPY ./requirements-plugins.txt /opt/netbox/
{% if dapp_netbox_plugins is defined %}
USER root
RUN /usr/local/bin/uv pip install -r /opt/netbox/requirements-plugins.txt
USER unit
{% endif %}

