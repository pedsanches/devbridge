import { visit } from 'unist-util-visit';
import type { Root, Element, Text, ElementContent } from 'hast';

/**
 * Rehype plugin to transform [[ID]] patterns into <smart-ref id="ID"> elements.
 * This enables the frontend to render interactive reference chips.
 */
export function rehypeSmartReferences() {
    return (tree: Root) => {
        visit(tree, 'text', (node: Text, index: number | undefined, parent: Element | Root | undefined) => {
            if (!node.value || !parent || !('children' in parent)) return;

            // Regex to find [R1] pattern (single brackets, R followed by numbers)
            // Captures the ID inside the brackets
            const citationRegex = /\[(R\d+)\]/g;

            if (!citationRegex.test(node.value)) return;

            const children: ElementContent[] = [];
            let lastIndex = 0;
            let match;

            // Reset regex to ensure we start from the beginning
            citationRegex.lastIndex = 0;

            while ((match = citationRegex.exec(node.value)) !== null) {
                const [fullMatch, id] = match;
                const matchIndex = match.index;

                // Push text before the match
                if (matchIndex > lastIndex) {
                    children.push({
                        type: 'text',
                        value: node.value.slice(lastIndex, matchIndex)
                    });
                }

                // Push the smart-ref element
                children.push({
                    type: 'element',
                    tagName: 'smart-ref',
                    properties: {
                        id: id
                    },
                    children: []
                });

                lastIndex = matchIndex + fullMatch.length;
            }

            // Push remaining text
            if (lastIndex < node.value.length) {
                children.push({
                    type: 'text',
                    value: node.value.slice(lastIndex)
                });
            }

            // Replace the original text node with our new children
            // We need to splice into the parent's children array
            parent.children.splice(index!, 1, ...children);
        });
    };
}
