.. js:attribute:: {{ name }}

   {% if type -%}
     **type:** {{ type|indent(3) }}
   {%- endif %}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {{ content|indent(3) }}

   {% if examples -%}
   :Examples:
   {% for example in examples -%}
     .. code-block:: js

     {{ example|indent(5) }}
   {% endfor %}
   {%- endif %}
