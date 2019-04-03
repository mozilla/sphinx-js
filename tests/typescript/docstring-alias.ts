/**
 * A definition of a class with aliases in the docstrings
 */
class AliasClassDefinition {
  /**
   * Constructor doc.
   *
   * This is a constructor with @arg and @argument as alias for @param
   * in its docstring
   * @arg simple {number} parameter with 'arg' as alias for param in its docstring
   * @argument simple2 {number} parameter with 'argument' as alias for param in its docstring
   */
  constructor(simple: number, simple2: number) {}

  /**
   * This is a method with @arg and @argument as alias for @param and
   * @return as alias for @returns in its docstring
   * @arg simple3 {number} parameter with 'arg' as alias for param in its docstring
   * @argument simple4 {number} parameter with 'argument' as alias for param in its docstring
   * @return number
   */
  alias_method(simple3: number, simple4: number): number {
    return simple3 + simple4;
  }
}
