/**
 * A definition of a class
 */
class ClassWithGenericMethod {
    /**
     * A generic method
     * @param arg a generic argument
     * @returns a value of the generic type
     */
    method<T>(arg:T) : T { return arg }
}