// Copyright (c) 2021 the Skulpt Project
// SPDX-License-Identifier: MIT

import { ASTVisitor } from "../ast/visitor.ts";
import { SymbolTableScope } from "../symtable/SymbolTableScope.ts";

/**
 * A BasicBlock is a unit of javascript code to be executed inside a switch case statement.
 * Basic blocks are an array of strings with a name and next property.
 * The strings will be joined in the final output to represent the full codeblock in the case statement
 */
export interface BasicBlock extends Array<string> {
    name: string;
    /** next points to the next instruction block */
    next: null | BasicBlock;
}

export interface CompilerUnit {
    readonly name: string;
    qualname: string /* dot-separated qualified name (lazy) */;
    readonly scopeType: number;
    consts: { [constant: string]: string };
    names: { [constant: string]: string };
    varnames: unknown;
    cellvars: unknown;
    freevars: unknown;
    private: unknown;

    argcount: number;
    posonlyargcount: number;
    kwonlyargcount: number;
    blocks: BasicBlock[];
    curblock: BasicBlock | null;

    fblock: unknown;

    firstlineno: number;
    lineno: number;
    colOffset: number;
}

export class CompilerUnit extends ASTVisitor {
    lineno = 0;
    consts: { [constant: string]: string } = {};
    names: { [constant: string]: string } = {};

    constructor(
        readonly space,
        readonly name: string,
        readonly firstLineNo: number,
        scope: SymbolTableScope,
        compilerInfo
    ) {
        super();
        this.varnames = Object.fromEntries(scope.varnames.map((name, i) => [name, i]));
        this.cellvars = Object.fromEntries(scope.varnames.map((name, i) => [name, i]));
    }
}
