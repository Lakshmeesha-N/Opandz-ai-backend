// src/agents/document_edit_agent/scripts/get_function_code.js

const fs = require("fs");
const parser = require("@babel/parser");

const filePath = process.argv[2];
const functionName = process.argv[3];

try {

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

    let targetFunction = null;

    function walk(node) {

        if (
            !node ||
            typeof node !== "object"
        ) {
            return;
        }

        if (
            node.type ===
            "FunctionDeclaration" &&
            node.id?.name ===
            functionName
        ) {

            targetFunction = {
                name: node.id.name,
                start: node.start,
                end: node.end,
                code: code.slice(
                    node.start,
                    node.end,
                ),
            };

            return;
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

    if (
        !targetFunction
    ) {

        throw new Error(
            `Function not found: ${functionName}`,
        );
    }

    process.stdout.write(
        JSON.stringify(
            targetFunction,
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