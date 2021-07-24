// Copyright (c) 2021 the Skulpt Project
// SPDX-License-Identifier: MIT

import type { Expression, mod, Module, stmt } from "../ast/astnodes.ts";
import { ASTKind } from "../ast/astnodes.ts";

const enum COMPILER_SCOPE {
    MODULE,
}

class SystemError extends Error {}

export class Compiler {
    free() {
        //
    }

    enterScope(name, scopeType, key, lineno) {}

    exitScope(name, scopeType, key, lineno) {}

    setQualname() {}

    newBlock() {}

    nextBlock() {}

    useNextBlock() {}

    body(stmts: stmt[]) {}

    mod(mod: mod) {
        this.enterScope("<module>", COMPILER_SCOPE.MODULE, mod, 0);
        let addNone = true;
        switch (mod._kind) {
            case ASTKind.Module:
                this.body((mod as Module).body);
                this.exitScope();
                break;
            case ASTKind.Interactive:
                throw new Error("interactive mode not supported");
            case ASTKind.Expression:
                this.visitExpr((mod as Expression).body);
                this.exitScope();
                addNone = false;
                break;
            default:
                throw new SystemError(`module kind ${mod._kind} should not be possible`);
        }
        const co = this.assemble(addNone);
        this.exitScope();
        return co;
    }
}
