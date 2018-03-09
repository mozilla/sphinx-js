.. js:function:: {{ name }}{{ params }}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {% for heads, tail in fields -%}
     :{{ heads|join(' ') }}: {{ tail }}
   {% endfor %}

   {% if examples -%}
   **Examples:**

   {% for example in examples -%}
   .. code-block:: js

      {{ example|indent(6) }}

   {% endfor %}
   {%- endif %}

   {{ content|indent(3) }}
