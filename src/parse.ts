import { GeneratedParser } from "./parser/generated_parser.ts";
import { Tokenizer } from "./tokenize/Tokenizer.ts";
import { tokenize } from "./tokenize/tokenize.ts";
import { readFile } from "./tokenize/readline.ts";
import { dump } from "./ast/ast.ts";
import { Colors, parse } from "../deps.ts";
import { getDiff } from "../support/diff.ts";
import { getPyAstDump } from "../support/py_ast_dump.ts";

const args = parse(Deno.args);

console.assert(args._.length == 1, Colors.bold(Colors.bgRed(Colors.white(" Must pass filename as argument "))));

const filename = args._[0] as string;

const tokens = tokenize(readFile(filename));

const tokenizer = new Tokenizer(tokens);

const parser = new GeneratedParser(tokenizer, args.verbose || false);

const ast = parser.file();

console.log();

console.log(Colors.bold(Colors.magenta("##### py #####")));
const pyDump = await getPyAstDump(Deno.readTextFileSync(filename), 2);
console.log(Colors.magenta(pyDump));

let jsDump = "";
if (ast !== null) {
    try {
        jsDump = dump(ast, 2) + "\n";
        console.log(Colors.bold(Colors.green("/**** js ****/")));
        console.log(Colors.green(jsDump));
    } catch {
        console.log("ast dump failed - JSON version");
        console.log(Colors.green(JSON.stringify(ast, null, 2)));
    }
} else {
    console.error("parser returned null");
}

console.log(getDiff(jsDump, pyDump));
