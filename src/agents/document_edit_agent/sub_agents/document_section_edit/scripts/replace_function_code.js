// src/agents/document_edit_agent/scripts/replace_function_code.js

const fs = require("fs");
const parser = require("@babel/parser");

const filePath = process.argv[2];
const functionName = process.argv[3];
const newFunctionCode = process.argv[4];

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

    let target = null;

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

            target = {
                start: node.start,
                end: node.end,
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

    if (!target) {

        throw new Error(
            `Function not found: ${functionName}`,
        );
    }

    const updatedCode =
        code.slice(
            0,
            target.start,
        ) +
        newFunctionCode +
        code.slice(
            target.end,
        );

    fs.writeFileSync(
        filePath,
        updatedCode,
        "utf8",
    );

    process.stdout.write(
        JSON.stringify(
            {
                success: true,
                function_name: functionName,
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