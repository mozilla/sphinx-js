.. js:attribute:: {{ name }}

   {% if deprecated -%}
   .. note::

      This attribute is deprecated.
      {% if deprecated is string -%}{{ deprecated }}{% endif -%}
   {%- endif %}

   {% if description -%}
     {{ description|indent(3) }}
   {%- endif %}

   {% if examples -%}
   **Examples:**

   {% for example in examples -%}
   .. code-block:: js

      {{ example|indent(6) }}
   {% endfor %}
   {%- endif %}

   {{ content|indent(3) }}
