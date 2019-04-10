/**
 * A definition of a class
 */
class ClassDefinition {
    /**
     * ClassDefinition constructor
     * @param simple A parameter with a simple type
     * @param complex A parameter with a complex type
     * @param args rest arguments
     */
    constructor(simple:number, complex:{[id:string]:any}, ...args:any[]) {

    }
    /**
     * This is a method without return type
     * @param simple A parameter with a simple type
     * @param complex A parameter with a complex type
     * @param args rest arguments
     */
    method1(simple:number, complex:{[id:string]:any}, ...args:any[]) : void {

    }
    /**
     * This is a method with a simple return type
     * @param simple A parameter with a simple type
     * @param complex A parameter with a complex type
     * @param args rest arguments
     * @returns 42
     */
    method2(simple:number, complex:{[id:string]:any}, ...args:any[]) : number {
        return 42;
    }
    /**
     * This is a method with a union type
     * @param union A parameter with a union type
     * @returns union
     */
    method3(union: number | string | any) : number | string | any{
        return union;
    }

    /** Read/write property/variable */
    property: any

    /** Read-only  or getter property */
    readonly property2: any

    /**
     * Property getter
     * @returns 42
     */
    get property3() : any {
        return 42
    }

    /**
     * Property setter
     * @param value new value of the property
     */
    set property4(value:any) {

    }
    /**
     * Index signature
     */
    [id:string]: any;
}