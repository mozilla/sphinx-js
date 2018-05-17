/**
 * A super interface
 */
interface ISuper {
    /**
     * A method
     * @param arg A value
     */
    method1(arg:number);
}

/**
 * A super class
 */
class Super {
    /**
     * A method
     * @param arg A value
     */
    method1(arg:number) { }
}

/**
 * A sub class
 */
class Sub extends Super {
    /**
     * Another method
     * @param arg A string
     */
    method2(arg:string) { }
}

/**
 * An interface extending a class
 */
interface ISub1 extends Super {
    /**
     * Another method
     * @param arg A string
     */
    method2(arg:string);
}

/**
 * An interface extending another interface
 */
interface ISub2 extends ISuper {
    /**
     * Another method
     * @param arg A string
     */
    method2(arg:string);
}