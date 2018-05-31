.. js:function:: {{ name }}{{ params }}

   {% if deprecated -%}
   .. note::

      This function is deprecated.
      {% if deprecated is string -%}{{ deprecated }}{% endif -%}
   {%- endif %}

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

   {% if see_also -%}
   .. seealso::

      {% for reference in see_also -%}
      - :any:`{{ reference }}`
      {% endfor %}
   {%- endif %}
