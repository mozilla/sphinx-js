{% macro deprecated(message) %}
{% if message -%}
.. note::

   Deprecated
   {%- if message is string -%}: {{ message }}{% else %}.{% endif -%}
{%- endif %}
{% endmacro %}

{% macro examples(items) %}
{% if items -%}
**Examples:**

{% for example in items -%}
.. code-block:: js

   {{ example|indent(3) }}
{% endfor %}
{%- endif %}
{% endmacro %}

{% macro see_also(items) %}
{% if items.internal or items.external -%}
.. seealso::

   {% for reference in items.internal -%}
   - :any:`{{ reference }}`
   {% endfor %}
   {% for reference in items.external -%}
   - {{ reference }}
   {% endfor %}
{%- endif %}
{% endmacro %}

{% macro exported_from(pathname) %}
{% if pathname -%}
    *exported from* :js:mod:`{{ pathname.dotted() }}`
{%- endif %}
{% endmacro %}
