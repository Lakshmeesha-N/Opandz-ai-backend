// src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/replace_multiple_functions_code.js
//
// Atomically replaces one or more named functions in a DOCX.js file.
//
// Usage:
//   node replace_multiple_functions_code.js <filePath> <replacementsJSON>
//
// replacementsJSON — JSON array of { name: string, code: string } objects.
//
// Outputs JSON to stdout: { success: true, replaced: [fn1, fn2, ...] }
// Writes to stderr + exits 1 on any error.

const fs = require("fs");
const parser = require("@babel/parser");

const filePath = process.argv[2];
const replacementsJSON = process.argv[3];

try {
    // ── 1. Parse the replacements list ──────────────────────────────────────
    let replacements;

    try {
        replacements = JSON.parse(replacementsJSON);
    } catch (e) {
        throw new Error(
            "Invalid replacementsJSON: " + e.message,
        );
    }

    if (!Array.isArray(replacements) || replacements.length === 0) {
        throw new Error(
            "replacementsJSON must be a non-empty array of { name, code } objects.",
        );
    }

    // Build a lookup map: functionName -> newCode
    const replacementMap = {};

    for (const item of replacements) {
        if (!item.name || typeof item.code !== "string") {
            throw new Error(
                "Each replacement must have { name: string, code: string }.",
            );
        }
        replacementMap[item.name] = item.code;
    }

    // ── 2. Read + parse the source file once ────────────────────────────────
    const code = fs.readFileSync(
        filePath,
        "utf8",
    );

    const ast = parser.parse(
        code,
        {
            sourceType: "module",
            plugins: [
                "jsx",
            ],
        },
    );

    // ── 3. Walk the AST and collect { name, start, end } for every target ───
    const targets = [];

    function walk(node) {
        if (
            !node ||
            typeof node !== "object"
        ) {
            return;
        }

        if (
            node.type === "FunctionDeclaration" &&
            node.id?.name &&
            replacementMap.hasOwnProperty(node.id.name)
        ) {
            targets.push({
                name: node.id.name,
                start: node.start,
                end: node.end,
            });
            // Don't descend — we captured this function already.
            return;
        }

        for (const key in node) {
            const value = node[key];

            if (Array.isArray(value)) {
                value.forEach(walk);
            } else if (
                value &&
                typeof value === "object"
            ) {
                walk(value);
            }
        }
    }

    walk(ast);

    // ── 4. Verify every requested function was found ─────────────────────────
    const foundNames = new Set(targets.map((t) => t.name));

    for (const item of replacements) {
        if (!foundNames.has(item.name)) {
            throw new Error(
                `Function not found: ${item.name}`,
            );
        }
    }

    // ── 5. Sort targets in REVERSE offset order ──────────────────────────────
    //
    // Replacing from the end of the file backwards means the byte offsets
    // of earlier targets remain valid after each splice.
    targets.sort(
        (a, b) => b.start - a.start,
    );

    // ── 6. Apply all replacements in one string-building pass ────────────────
    let updatedCode = code;

    for (const target of targets) {
        updatedCode =
            updatedCode.slice(0, target.start) +
            replacementMap[target.name] +
            updatedCode.slice(target.end);
    }

    // ── 7. Write the file once ───────────────────────────────────────────────
    fs.writeFileSync(
        filePath,
        updatedCode,
        "utf8",
    );

    // ── 8. Report success ────────────────────────────────────────────────────
    process.stdout.write(
        JSON.stringify({
            success: true,
            replaced: targets.map((t) => t.name),
        }),
    );

} catch (error) {
    process.stderr.write(error.message);
    process.exit(1);
}
