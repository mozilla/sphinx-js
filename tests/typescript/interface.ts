/**
 * A definition of an interface
 */
interface IDefinition {
    /**
     * This is a method without return type
     * @param simple A parameter with a simple type
     * @param complex A parameter with a complex type
     * @param args rest arguments
     */
    method1(simple:number, complex:{[id:string]:any}, ...args:any[]) : void;
    /**
     * This is a method with a simple return type
     * @param simple A parameter with a simple type
     * @param complex A parameter with a complex type
     * @param args rest arguments
     */
    method2(simple:number, complex:{[id:string]:any}, ...args:any[]) : number;

    /** Read/write property/variable */
    property: any

    /** Read-only  or getter property */
    readonly property2: any

    /** 
     * Call signature
     * @param arg1 argument to the call signature
     */
    (arg1:any) : void;

    /**
     * Index signature
     */
    [id:string]: any
}