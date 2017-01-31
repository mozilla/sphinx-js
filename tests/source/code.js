/**
 * Return the ratio of the inline text length of the links in an element to
 * the inline text length of the entire element.
 * @param {node} A node of some kind
 */
function linkDensity(node) {
    const length = node.flavors.get('paragraphish').inlineLength;
    const lengthWithoutLinks = inlineTextLength(node.element,
                                                element => element.tagName !== 'A');
    return (length - lengthWithoutLinks) / length;
}
