interface A {
    a: number;
}

interface B {
    b: number;
}

/**
 * Generic class with a type constraint
 * @param T Type extending A
 */
class GenericConstraint<T extends A> {
    t: T;

    /**
     * A generic method with a type constraint
     * @param arg An argument of type U
     */
    method<U extends B>(arg: U) {
        return arg;
    };
}
