PLUGINS = [
{% for plugin in dapp_netbox_plugins.keys() %}
        "{{ (dapp_netbox_plugins[plugin]['name']) if (dapp_netbox_plugins[plugin]['name'] is defined) else plugin }}",
{% endfor %}
]

PLUGINS_CONFIG = {
{% for plugin in dapp_netbox_plugins.keys() %}
{% if dapp_netbox_plugins[plugin]['config'] is defined %}
        "{{ (dapp_netbox_plugins[plugin]['name']) if (dapp_netbox_plugins[plugin]['name'] is defined) else plugin }}": {
            {% for option,value in dapp_netbox_plugins[plugin]['config'].items() %}
            "{{ option }}": {{ (value | string | capitalize) if value is boolean else (value | to_json) }},
            {% endfor %}
        }
{% endif %}
{% endfor %}
}
