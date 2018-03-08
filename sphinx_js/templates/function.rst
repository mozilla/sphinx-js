.. js:function:: {{ name }}{{ params }}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {% for heads, tail in fields -%}
     :{{ heads|join(' ') }}: {{ tail }}
   {% endfor %}

   {{ content|indent(3) }}

   {% if examples -%}
   :Examples:
   {% for example in examples -%}
     .. code-block:: js

     {{ example|indent(5) }}
   {% endfor %}
   {%- endif %}
