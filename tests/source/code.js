/**
 * Return the ratio of the inline text length of the links in an element to
 * the inline text length of the entire element.
 *
 * @param {Node} node - Something of a single type
 * @throws {PartyError|FartyError} Something with multiple types and a line
 *    that wraps
 * @returns {Number} What a thing
 */
function linkDensity(node) {
    const length = node.flavors.get('paragraphish').inlineLength;
    const lengthWithoutLinks = inlineTextLength(node.element,
                                                element => element.tagName !== 'A');
    return (length - lengthWithoutLinks) / length;
}

/**
 * Class doc.
 */
class ContainingClass {
    /**
     * Constructor doc.
     *
     * @arg ho A thing
     */
    constructor(ho) {
        /**
         * A var
         */
        this.someVar = 4;
    }

    /**
     * Here.
     * @protected
     */
    someMethod(hi) {
    }

    /**
     * Setting this also frobs the frobnicator.
     */
    get bar() {
      return this._bar;
    }
    set bar(baz) {
      this._bar = _bar;
    }

    /**
     * Private thing.
     * @private
     */
    secret() {}
}

// We won't add any new members to this class, because it would break some tests.
/** Closed class. */
class ClosedClass {
    /**
     * Public thing.
     */
    publical() {}

    /**
     * Public thing 2.
     */
    publical2() {}

    /**
     * Public thing 3.
     */
    publical3() {}
}

/** Non-alphabetical class. */
class NonAlphabetical {
    /** Fun z. */
    z() {}

    /** Fun a. */
    a() {}
}

/**
 * This doesn't emit a paramnames key in meta.code.
 * @class
 */
const NoParamnames = {};

/** Thing to be shadowed in more_code.js */
function shadow() {}

/**
 * Object initializer "class" definition in literal notation.
 * @see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Object_initializer
 * @class
 */
var ObjectLiteralClass = {
    /**
     * Foos the bars.
     * @param {string} bar - the Bar to Foo.
     * @returns {string} - Returns the Foo'd Bar.
     */
    foo(bar) {
        return bar;
    }
}

/**
 * Private class renamed as public class, using the jsdoc lends tag.
 *
 * A common pattern in some codebases is to have a public class which
 * forwards to a private class, where the jsdoc annotations live.
 *
 * @lends PublicClass
 */
class PrivateClass {
    /**
     * This is the method we want to appear on the public API.
     * @param {string} foo - We want the foo.
     */
    public(foo) {
        return foo;
    }

    /**
     * This is a private method which should *not* appear on the public API.
     * @param {string} foo - Gotta have that foo.
     * @private
     */
    private(foo) {
        return foo
    }
}

/**
 * This is the public API. All methods forward to PrivateClass.
 */
class PublicClass {
    constructor() {
        this._privateClass = new PrivateClass();
    }

    /**
     * This should *not* appear in the documentation.
     *
     * @param {string} foo - You don't want this foo.
     * @private
     */
    public(foo) {
        return this._privateClass(foo);
    }
}

/**
 * Private class renamed as public class, using the jsdoc lends tag.
 * Same as above but using object initializer written in literal object
 * notation.
 *
 * A common pattern in some codebases is to have a public class which
 * forwards to a private class, where the jsdoc annotations live.
 *
 * @lends PublicObjectLiteral
 */
var PrivateObjectLiteral = {
    /**
     * This is the method we want to appear on the public API.
     * @param {string} foo - We want the foo.
     */
    public(foo) {
        return foo;
    },

    /**
     * This is a private method which should *not* appear on the public API.
     * @param {string} foo - Gotta have that foo.
     * @private
     */
    private(foo) {
        return foo
    }
}

/**
 * This is the public API. All methods forward to PrivateClass.
 */
var PublicObjectLiteral = {
    _privateClass: new PrivateClass(),

    /**
     * This should *not* appear in the documentation.
     *
     * @param {string} foo - You don't want this foo.
     * @private
     */
    public(foo) {
        return this._privateClass(foo);
    }
}
