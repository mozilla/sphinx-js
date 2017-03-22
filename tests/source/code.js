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
