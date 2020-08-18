class Superclass {
  method() {
  }
}

interface SuperInterface {
}

interface Interface extends SuperInterface {
}

interface InterfaceWithMembers {
  callableProperty(): void;
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

class ClassWithProperties {
  static someStatic: number;
  someOptional?: number;
  private somePrivate: number;
  /**
   * This is totally normal!
   */
  someNormal: number;

  constructor(a: number) {
  }

  get gettable(): number {
    return 5;
  }

  set settable(value: string) {
  }
}

class Indexable {
  [id:string]: any;  // smoketest
}
