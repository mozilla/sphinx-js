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
{% if items -%}
.. seealso::

   {% for reference in items -%}
   - :any:`{{ reference }}`
   {% endfor %}
{%- endif %}
{% endmacro %}
