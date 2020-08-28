{% import 'common.rst' as common %}

.. js:class:: {{ name }}{{ params }}

   {{ common.deprecated(deprecated)|indent(3) }}

   {% if class_comment -%}
     {{ class_comment|indent(3) }}
   {%- endif %}

   {% if is_abstract -%}
     *abstract*
   {%- endif %}

   {% if is_interface -%}
     *interface*
   {%- endif %}

   {{ common.exported_from(exported_from)|indent(3) }}

   {% if supers -%}
     **Extends:**
       {% for super in supers -%}
         - :js:class:`~{{ super.dotted() }}`
       {% endfor %}
   {%- endif %}

   {% if interfaces -%}
     **Implements:**
       {% for interface in interfaces -%}
         - :js:class:`~{{ interface.dotted() }}`
       {% endfor %}
   {%- endif %}

   {% if constructor_comment -%}
     {{ constructor_comment|indent(3) }}
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
