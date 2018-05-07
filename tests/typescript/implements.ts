/**
 * A definition of an interface
 */
interface Interface {
    /**
     * A method specification
     * @param arg A value
     */
    method(arg:number):void;

    /**
     * Another documented method
     * @param arg A string
     * @returns A string
     */
    documented(arg:string) : string;
}

/**
 * An implementation of an interface
 */
class Implementation implements Interface {
    /**
     * A method implementation
     * @param arg A value
     */
    method(arg:number) { }

    // Is this documented?
    documented(arg:string) : string {
        return arg;
    }
}