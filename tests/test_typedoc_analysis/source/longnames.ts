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
  "weird#Var": number;

  constructor (num: number) {
    this.numInstanceVar = num;
  }

  someMethod(): void {
  }
}

interface Face {
  moof: string;
}

const smack = {
  /**
   * Whacker
   */
  whack: 3
};

const Person = function() {
    /**
     * Inner function
     */
    function say() {
        return "I'm inner.";
    }
};
