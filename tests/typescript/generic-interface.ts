/**
 * A definition of a generic interface
 */
interface GenericInterface<T> {
    /**
     * Generic member type
     */
    member: T

    /**
     * This is a method with a generic return type
     * @returns 42
     */
    method2(): T
}