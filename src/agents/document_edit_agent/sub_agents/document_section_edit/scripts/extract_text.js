// src/agents/document_edit_agent/sub_agents/document_section_edit/scripts/extract_text.js
//
// Extracts all TextRun strings from every exported build_* function in a DOCX.js file.
//
// Usage:
//   node extract_text.js <filePath>
//
// Outputs JSON to stdout:
//   [{ "section": "build_header", "text": "line1\nline2" }, ...]

const fs = require("fs");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

const filePath = process.argv[2];

if (!filePath) {
    process.stderr.write("Usage: node extract_text.js <docxjs_file>");
    process.exit(1);
}

try {
    const code = fs.readFileSync(filePath, "utf8");

    const ast = parser.parse(code, {
        sourceType: "module",
        plugins: ["typescript", "jsx"],
    });

    const sections = [];

    traverse(ast, {
        ExportNamedDeclaration(path) {
            const declaration = path.node.declaration;

            if (
                !declaration ||
                declaration.type !== "FunctionDeclaration"
            ) {
                return;
            }

            const functionName = declaration.id.name;

            if (!functionName.startsWith("build_")) {
                return;
            }

            const texts = [];

            path.traverse({
                NewExpression(innerPath) {
                    const node = innerPath.node;

                    if (
                        node.callee.type !== "Identifier" ||
                        node.callee.name !== "TextRun"
                    ) {
                        return;
                    }

                    const arg = node.arguments[0];

                    if (!arg) return;

                    // new TextRun("Hello")
                    if (arg.type === "StringLiteral") {
                        texts.push(arg.value);
                        return;
                    }

                    // new TextRun({ text: "Hello", bold: true })
                    if (arg.type === "ObjectExpression") {
                        for (const property of arg.properties) {
                            if (
                                property.type === "ObjectProperty" &&
                                property.key.type === "Identifier" &&
                                property.key.name === "text" &&
                                property.value.type === "StringLiteral"
                            ) {
                                texts.push(property.value.value);
                            }
                        }
                    }
                },
            });

            sections.push({
                section: functionName,
                text: texts.join("\n"),
            });
        },
    });

    process.stdout.write(JSON.stringify(sections));

} catch (error) {
    process.stderr.write(error.message);
    process.exit(1);
}
