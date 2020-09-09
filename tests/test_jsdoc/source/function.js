/**
 * Determine any of type, note, score, and element using a callback. This
 * overrides any previous call.
 *
 * The callback should return...
 *
 * * An optional :term:`subscore`
 * * A type (required on ``dom(...)`` rules, defaulting to the input one on
 *   ``type(...)`` rules)
 * * Optional notes
 * * An element, defaulting to the input one. Overriding the default
 *   enables a callback to walk around the tree and say things about nodes
 *   other than the input one.
 *
 * @param {String} bar Which bar
 * @param baz
 * @return {Number} How many things
 *     there are
 * @exception ExplosionError It went boom.
 */
function foo(bar, baz=8) {}
