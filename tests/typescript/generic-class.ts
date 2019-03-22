/**
 * A definition of a generic class
 */
class GenericClass<T> {
    /**
     * Generic member type
     */
    member:T

    /**
     * GenericClass constructor
     * @param arg Generic as argument
     */
    constructor(arg: T) {
    	this.member = arg
    }

    /**
     * This is a method with a generic return type
     * @returns 42
     */
    method2(): T {
        return this.member
    }
}