// src/agents/document_edit_agent/scripts/parse_ast.js

const parser = require("@babel/parser");

const code = process.argv[2];

try {

    const ast = parser.parse(
        code,
        {
            sourceType: "module",
            plugins: [
                "jsx",
            ],
        },
    );

    const functions = [];

    function walk(node) {

        if (!node || typeof node !== "object") {
            return;
        }

        if (
            node.type === "FunctionDeclaration"
        ) {

            functions.push(
                {
                    name: node.id?.name,
                    start: node.start,
                    end: node.end,
                },
            );
        }

        for (const key in node) {

            const value = node[key];

            if (
                Array.isArray(
                    value,
                )
            ) {

                value.forEach(
                    walk,
                );
            }

            else if (
                value &&
                typeof value ===
                "object"
            ) {

                walk(
                    value,
                );
            }
        }
    }

    walk(
        ast,
    );

    process.stdout.write(
        JSON.stringify(
            {
                functions,
            },
        ),
    );

}

catch (error) {

    process.stderr.write(
        error.message,
    );

    process.exit(
        1,
    );
}