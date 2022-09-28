// Copyright (c) 2021 the Skulpt Project
// SPDX-License-Identifier: MIT

import { ASTVisitor } from "../ast/visitor.ts";
import { SymbolTableScope } from "../symtable/SymbolTableScope.ts";
import { assert } from "../util/assert.ts";
import { Ops } from "./opcodes.ts";

class Instruction {
    lineno = 0;
    hasJump = false;
    constructor(public opcode: Ops, public arg = 0) {
        if (this.opcode < Ops.HAVE_ARGUMENT) {
            assert(arg === 0);
        }
    }

    size() {}

    encode() {}

    jumpTo() {}

    toString() {}
}

class Block {
    instructions: Instruction[] = [];
    nextBlock: Block | null = null;
    marked = false;
    haveReturn = false;
    autoInsertReturn = false;

    _postOrderSee(stack: Block[], nextblock: Block) {
        if (!nextblock.marked) {
            nextblock.marked = true;
            stack.push(nextblock);
        }
    }

    postOrder() {}

    codeSize() {}

    getCode() {}
}
export class PythonCodeMaker extends ASTVisitor {
    names = {};
    consts = {};
    constsReal = [];
    argcount = 0;
    posonlyargcount = 0;
    kwonlyargcount = 0;
    linenoSet = false;
    lineno = 0;
    addNoneToFinalRetur = true;

    firstBlock: Block;
    currentBlock: Block;
    instrs: Instruction[];

    constructor(public name: string, public firstLineNo: number, public scope: SymbolTableScope, public compileInfo) {
        super();
        this.firstBlock = this.newBlock();
        this.currentBlock = this.firstBlock;
        this.instrs = this.firstBlock.instructions;
        this.useBlock(this.firstBlock);
        this.varNames = Object.fromEntries(scope.varnames.map((s, i) => [s, i]));
        this.cellVars = null;
        // sort scope.free_vars;
        this.freeVars = null;
    }

    newBlock() {
        return new Block();
    }

    useBlock(block: Block) {
        this.currentBlock = block;
        this.instrs = block.instructions;
    }

    useNextBlock(block: null | Block = null) {
        if (block === null) {
            block = this.newBlock();
        }
        this.currentBlock!.nextBlock = block;
        this.useBlock(block);
        return block;
    }

    isDeadCode() {
        return this.currentBlock.haveReturn;
    }

    emitOp(op: Ops) {
        const instr = new Instruction(op);
        if (!this.linenoSet) {
            instr.lineno = this.lineno;
            this.linenoSet = true;
        }
        if (!this.isDeadCode()) {
            this.instrs.push(instr);
        }
    }
}
