/**
 * A definition of a generic class
 */
class GenericClass<T> {
    /**
     * GenericClass constructor
     * @param arg Generic as argument
     */
    constructor(arg:T) {

    }

    /**
     * Generic member type
     */
    member:T

    /**
     * This is a method with a generic return type
     * @returns 42
     */
    method2() : T {
    }
}