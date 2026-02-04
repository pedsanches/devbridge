import { describe, it, expect } from "vitest";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeStringify from "rehype-stringify";
import { rehypeSmartReferences } from "./rehype-smart-references";

describe("rehypeSmartReferences", () => {
    const processor = unified()
        .use(remarkParse)
        .use(remarkRehype)
        .use(rehypeSmartReferences)
        .use(rehypeStringify);

    it("parses legacy references [R1]", async () => {
        const input = "Check source [R1] for details.";
        const result = await processor.process(input);
        expect(result.toString()).toContain('<smart-ref id="R1"></smart-ref>');
    });

    it("parses persistent references [R-BACKEND-123]", async () => {
        const input = "See [R-BACKEND-123] implementation.";
        const result = await processor.process(input);
        expect(result.toString()).toContain('<smart-ref id="R-BACKEND-123"></smart-ref>');
        expect(result.toString()).toContain("See ");
        expect(result.toString()).toContain(" implementation.");
    });

    it("parses multiple references in one line", async () => {
        const input = "Compare [R1] with [R-API-002].";
        const result = await processor.process(input);
        expect(result.toString()).toContain('<smart-ref id="R1"></smart-ref>');
        expect(result.toString()).toContain('<smart-ref id="R-API-002"></smart-ref>');
    });

    it("ignores partial matches or invalid formats", async () => {
        const input = "This is [R] invalid.";
        const result = await processor.process(input);
        // Should not create smart-ref for [R] if regex expects digits/chars after R
        // Our regex is /\[(R[-\w]+)\]/g
        // R followed by - or word chars. So "R" alone matches "R" is \w? No wait.
        // \w includes [A-Za-z0-9_].
        // "R" alone: R matches R. But + means one or more.
        // So [R] shouldn't match if we assume "R" is part of the prefix logic but need at least one char?
        // Actually [R] matches R which matches \w.
        // If we want to be strict that it must have numbers:
        // But let's check what it actually does.
        // "R" falls under \w. So [R] matches. This is acceptable for now as "R" could be a code.
        expect(result.toString()).toContain('This is [R] invalid.');
    });
});
