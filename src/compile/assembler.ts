// Copyright (c) 2021 the Skulpt Project
// SPDX-License-Identifier: MIT

import { ASTVisitor } from "../ast/visitor.ts";

export class PythonCodeMaker extends ASTVisitor {
    constructor() {
        super();
    }

    newBlock() {}
}
