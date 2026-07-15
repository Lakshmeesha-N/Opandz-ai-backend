// scripts/extract_text.js

const fs = require("fs");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

const filePath = process.argv[2];

if (!filePath) {
    console.error("Usage: node extract_text.js <docxjs_file>");
    process.exit(1);
}

const code = fs.readFileSync(filePath, "utf8");

const ast = parser.parse(code, {
    sourceType: "module",
    plugins: ["typescript", "jsx"],
});

const texts = [];

traverse(ast, {
    NewExpression(path) {
        const node = path.node;

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

// Remove empty lines and trim whitespace
const cleanText = texts
    .map(t => t.trim())
    .filter(Boolean)
    .join("\n");

console.log(cleanText);