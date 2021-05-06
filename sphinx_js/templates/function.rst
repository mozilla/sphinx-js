{% import 'common.rst' as common %}

{% if is_static %}
.. js:staticfunction:: {{ name }}{{ '?' if is_optional else '' }}{{ params }}
{% else %}
.. js:function:: {{ name }}{{ '?' if is_optional else '' }}{{ params }}
{% endif %}

   {{ common.deprecated(deprecated)|indent(3) }}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {% for heads, tail in fields -%}
     :{{ heads|join(' ') }}: {{ tail }}
   {% endfor %}

   {{ common.examples(examples)|indent(3) }}

   {{ content|indent(3) }}

   {{ common.see_also(see_also)|indent(3) }}
