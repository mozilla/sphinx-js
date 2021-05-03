{% import 'common.rst' as common %}

.. js:namespace:: {{ name }}{{ params }}

   {{ common.deprecated(deprecated)|indent(3) }}

   {% if namespace_comment -%}
     {{ namespace_comment|indent(3) }}
   {%- endif %}

   {{ common.exported_from(exported_from)|indent(3) }}

   {% for heads, tail in fields -%}
     :{{ heads|join(' ') }}: {{ tail }}
   {% endfor %}

   {{ common.examples(examples)|indent(3) }}

   {{ content|indent(3) }}

   {% if members -%}
     {{ members|indent(3) }}
   {%- endif %}

   {{ common.see_also(see_also)|indent(3) }}
