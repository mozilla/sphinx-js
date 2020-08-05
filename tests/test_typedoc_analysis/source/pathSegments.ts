/**
 * Function
 */
function foo(): void {
  /**
   * An inner function
   */
  function inner(): void {
  }
}
foo.adHocInner = 'innerValue';

/**
 * Foo class
 */
class Foo {
  /**
   * Static member
   */
  static staticMember = 8;

  /**
   * Num instance var
   */
  numInstanceVar: number;

  /**
   * Weird var
   */
  "weird#Var": number;

  /**
   * Constructor
   */
  constructor (num: number) {
    this.numInstanceVar = num;
  }

  /**
   * Method
   */
  someMethod(): void {
  }

  /**
   * Static method
   */
  static staticMethod(): void {
  }

  /**
   * Getter
   */
  get getter(): number {
    return 5;
  }

  /**
   * Setter
   */
  set setter(n: number) {
  }
}

interface Face {
  /**
   * Interface property
   */
  moof: string;
}

namespace SomeSpace {
  /**
   * Namespaced number
   */
  const spacedNumber = 4;
}
