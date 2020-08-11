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
