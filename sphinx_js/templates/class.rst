.. js:class:: {{ name }}{{ params }}

   {% if class_comment -%}
     {{ class_comment|indent(3) }}
   {%- endif %}

   {% if constructor_comment -%}
     {{ constructor_comment|indent(3) }}
   {%- endif %}

   {% for heads, tail in fields -%}
     :{{ heads|join(' ') }}: {{ tail }}
   {% endfor %}

   {{ content|indent(3) }}


