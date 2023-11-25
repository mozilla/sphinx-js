{% import 'common.rst' as common %}

.. js:data:: {{ name }}

   {{ common.deprecated(deprecated)|indent(3) }}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {% for heads, tail in fields -%}
     :{{ heads|join(' ') }}: {{ tail }}
   {% endfor %}

   {{ common.examples(examples)|indent(3) }}

   {{ content|indent(3) }}

   {% if members -%}
     {{ members|indent(3) }}
   {%- endif %}

   {{ common.see_also(see_also)|indent(3) }}
