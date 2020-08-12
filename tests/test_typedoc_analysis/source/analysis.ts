class Superclass {
  method() {
  }
}

interface SuperInterface {
}

interface Interface extends SuperInterface {
}

/**
 * An empty subclass
 */
export abstract class EmptySubclass extends Superclass implements Interface {
}

const topLevelConst = 3;

/**
 * @param a Some number
 * @param b Some strings
 * @return The best number
 */
function func(a: number = 1, ...b: string[]): number {
  return 4;
}

class ClassWithMethods {
  constructor(a: number) {
  }
}
