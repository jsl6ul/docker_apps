FROM netboxcommunity/netbox:{{ dapp_netbox_version }}
COPY ./requirements-plugins.txt /opt/netbox/
{% if dapp_netbox_plugins is defined %}
USER root
{% for plugin in dapp_netbox_plugins %}
{% if dapp_netbox_plugins[plugin]['pre_install'] is defined %}
{% for cmd in dapp_netbox_plugins[plugin]['pre_install'] %}
RUN {{ cmd }}
{% endfor %}
{% endif %}
{% endfor %}
RUN /usr/local/bin/uv pip install -r /opt/netbox/requirements-plugins.txt
{% for plugin in dapp_netbox_plugins %}
{% if dapp_netbox_plugins[plugin]['post_install'] is defined %}
{% for cmd in dapp_netbox_plugins[plugin]['post_install'] %}
RUN {{ cmd }}
{% endfor %}
{% endif %}
{% endfor %}
USER unit
{% endif %}

