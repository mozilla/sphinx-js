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

   {% if examples -%}
   **Examples:**

   {% for example in examples -%}
   .. code-block:: js

      {{ example|indent(6) }}
   {% endfor %}
   {%- endif %}

   {{ content|indent(3) }}

   {% if members -%}
     {{ members|indent(3) }}
   {%- endif %}
