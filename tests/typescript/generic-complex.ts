/**
 * A definition of a class, using generic types containing unions and lists
 */
class ClassWithComplexGenericMethodArgs {
    /**
     * A generic method
     * @param arg a generic argument
     * @returns a value of the generic type
     */
    async method<T>(arg: Partial<T|number>): Promise<[Partial<T|number>, number]> {
        return [arg, 1];
    }
}