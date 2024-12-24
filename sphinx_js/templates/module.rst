{% import 'common.rst' as common %}

.. js:module:: {{ name }}

{{ common.deprecated(deprecated) }}

{% if description -%}
    {{ description }}
{%- endif %}

{% if authors -%}
    **Author(s):** {% for a in authors -%}
                       {% if loop.last -%}{{ a }}{% else %}{{ a }}, {% endif %}
                   {%- endfor %}
{%- endif %}

{% if version -%}
    **Version:** {{ version }}
{%- endif %}

{% if license_information -%}
    **License:** {{ license_information }}
{%- endif %}

{% if members -%}
    {{ members }}
{%- endif %}
