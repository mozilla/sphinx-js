/**
 * A definition of a class
 */
class ClassDefinition {
    field: string;

    /**
     * ClassDefinition constructor
     * @param simple A parameter with a simple type
     */
    constructor(simple: number) {

    }

    /**
     * This is a method without return type
     * @param simple A parameter with a simple type
     */
    method1(simple: number) : void {

    }

    /**
     * This is a method (should be before method 'method1', but after fields)
     */
    anotherMethod() {

    }

    /**
     * This is an overloaded method (1).
     */
    overloaded(arg: number): number;

    /**
     * This is an overloaded method (2).
     */
    overloaded(arg: string): string;

    overloaded(arg: number | string): number | string {
        return arg;
    }
}
