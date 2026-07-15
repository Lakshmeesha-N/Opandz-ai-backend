// src/agents/document_edit_agent/scripts/validate_docxjs.js

const fs = require("fs");
const parser = require("@babel/parser");

const filePath = process.argv[2];

try {

    const code = fs.readFileSync(
        filePath,
        "utf8",
    );

    parser.parse(
        code,
        {
            sourceType: "module",
            plugins: [
                "jsx",
            ],
            errorRecovery: false,
        },
    );

    process.stdout.write(
        JSON.stringify(
            {
                valid: true,
                error: null,
            },
        ),
    );

}

catch (error) {

    process.stdout.write(
        JSON.stringify(
            {
                valid: false,
                error: error.message,
                line: error.loc?.line ?? null,
                column: error.loc?.column ?? null,
            },
        ),
    );

}