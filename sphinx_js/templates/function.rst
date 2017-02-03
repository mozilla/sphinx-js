.. function:: {{ name }}{{ params }}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {{ content|indent(3) }}


