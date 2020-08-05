/**
 * Foo function.
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

  constructor (num: number) {
    this.numInstanceVar = num;
  }

  someMethod(): void {
  }
}

interface Face {
  /**
   * Interface property
   */
  moof: string;
}
