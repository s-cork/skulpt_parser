import token
from typing import Any, Dict, Optional, IO, Text, Tuple
from io import StringIO
from pegen.grammar import (
    Cut,
    GrammarVisitor,
    NameLeaf,
    StringLeaf,
    Rhs,
    NamedItem,
    Lookahead,
    PositiveLookahead,
    NegativeLookahead,
    Opt,
    Repeat0,
    Repeat1,
    Gather,
    Group,
    Rule,
    Alt,
)
from pegen import grammar
from pegen.parser_generator import ParserGenerator

# @TODO here are the missing types returned from the methods
# we should include these in the import somehow
# see pegen.h for the missing type definitions
[
    "Token",
    "SlashWithDefault",
    "StarEtc",
    "NameDefaultPair",
    "CmpopExprPair",
    "KeyValuePair",
    "KeywordOrStarred",  # found this one @stu! :D
]

MODULE_PREFIX = """\
// #!/usr/bin/env python3.8
// # @generated by pegen from {filename}
// @ts-nocheck

import * as ast from "../ast/ast.ts";
import * as astnodes from "../ast/astnodes.ts";
import {{ mod, expr, stmt, operator, alias, withitem, excepthandler, arguments_, arg, comprehension }} from "../ast/astnodes.ts";
import * as pegen_real from "./pegen.ts";
import {{ Colors }} from "../../deps.ts";

import {{memoize, memoize_left_rec, logger, Parser}} from "./parser.ts";

const EXTRA = []; // todo

const pegen = new Proxy(pegen_real, {{
    get(target, prop, receiver) {{
        if (prop in target) {{
            return (...args) => {{
                const [head, ...tail] = args;
                console.log(Colors.green("Calling '" + prop + "'"));
                console.log(Colors.green("With"), tail);
                return target[prop](...args);
            }};
        }}

        console.log(Colors.yellow("Missing pegen func!: " + prop));

        return (...args) => args
    }}
}});
"""

MODULE_SUFFIX = """

"""

# todo mangle names like await
reserved = {"await"}


def fix_reserved(name):
    return name + "_" if name in reserved else name


non_exact_tok = (
    "AWAIT",
    "OP",
    "ERRORTOKEN",
    "TYPE_IGNORE",
    "TYPE_COMMENT",
    "NL",
    "NUMBER",
    "STRING",
    "NAME",
    "ASYNC",
    "COMMENT",
    "ENCODING",
    "ENDMARKER",
    "NEWLINE",
    "INDENT",
    "DEDENT",
)


class PythonCallMakerVisitor(GrammarVisitor):
    def __init__(self, parser_generator: ParserGenerator):
        self.gen = parser_generator
        self.cache: Dict[Any, Any] = {}

    def visit_NameLeaf(self, node: NameLeaf) -> Tuple[Optional[str], str]:
        name = node.value
        if name in ("NAME", "NUMBER", "STRING", "OP"):
            name = name.lower()
            return name, f"this.{name}()"
        if name in non_exact_tok:
            return name.lower(), f"this.expect({name!r})"
        return name, f"this.{name}()"

    def visit_StringLeaf(self, node: StringLeaf) -> Tuple[str, str]:
        return "literal", f"this.expect({node.value})"

    def visit_Rhs(self, node: Rhs) -> Tuple[Optional[str], str]:
        if node in self.cache:
            return self.cache[node]
        if len(node.alts) == 1 and len(node.alts[0].items) == 1:
            self.cache[node] = self.visit(node.alts[0].items[0])
        else:
            name = self.gen.name_node(node)
            self.cache[node] = name, f"this.{name}()"
        return self.cache[node]

    def visit_NamedItem(self, node: NamedItem) -> Tuple[Optional[str], str]:
        name, call = self.visit(node.item)
        if node.name:
            name = node.name
        return name, call

    def lookahead_call_helper(self, node: Lookahead) -> Tuple[str, str]:
        name, call = self.visit(node.node)
        head, tail = call.split("(", 1)
        assert tail[-1] == ")"
        tail = tail[:-1]
        return head, tail

    def visit_PositiveLookahead(self, node: PositiveLookahead) -> Tuple[None, str]:
        head, tail = self.lookahead_call_helper(node)
        return None, f"this.positive_lookahead({head}, {tail})"

    def visit_NegativeLookahead(self, node: NegativeLookahead) -> Tuple[None, str]:
        head, tail = self.lookahead_call_helper(node)
        return None, f"this.negative_lookahead({head}, {tail})"

    def visit_Opt(self, node: Opt) -> Tuple[str, str]:
        name, call = self.visit(node.node)
        # Note trailing comma (the call may already have one comma
        # at the end, for example when rules have both repeat0 and optional
        # markers, e.g: [rule*])
        if call.endswith(","):
            return "opt", call
        else:
            return "opt", f"{call}, 1"

    def visit_Repeat0(self, node: Repeat0) -> Tuple[str, str]:
        if node in self.cache:
            return self.cache[node]
        name = self.gen.name_loop(node.node, False)
        self.cache[node] = name, f"this.{name}()"  # Also a trailing comma!
        return self.cache[node]

    def visit_Repeat1(self, node: Repeat1) -> Tuple[str, str]:
        if node in self.cache:
            return self.cache[node]
        name = self.gen.name_loop(node.node, True)
        self.cache[node] = name, f"this.{name}()"  # But no trailing comma here!
        return self.cache[node]

    def visit_Gather(self, node: Gather) -> Tuple[str, str]:
        if node in self.cache:
            return self.cache[node]
        name = self.gen.name_gather(node)
        self.cache[node] = name, f"this.{name}()"  # No trailing comma here either!
        return self.cache[node]

    def visit_Group(self, node: Group) -> Tuple[Optional[str], str]:
        return self.visit(node.rhs)

    def visit_Cut(self, node: Cut) -> Tuple[str, str]:
        self.gen.has_cut = True
        self.gen.args.add("cut")
        return "cut", "true"


class PythonParserGenerator(ParserGenerator, GrammarVisitor):
    def __init__(
        self,
        grammar: grammar.Grammar,
        file: Optional[IO[Text]],
        tokens: Dict[int, str] = token.tok_name,
    ):
        super().__init__(grammar, tokens, file)
        self.suffix = MODULE_SUFFIX
        self.callmakervisitor = PythonCallMakerVisitor(self)

    def generate(self, filename: str) -> None:
        header = self.grammar.metas.get("header", MODULE_PREFIX)
        if header is not None:
            self.print(header.rstrip("\n").format(filename=filename))
        subheader = self.grammar.metas.get("subheader", "")
        if subheader:
            self.print(subheader.format(filename=filename))
        self.print("\n")
        self.print("export class GeneratedParser extends Parser {")
        while self.todo:
            for rulename, rule in list(self.todo.items()):
                del self.todo[rulename]
                self.print()
                with self.indent():
                    self.visit(rule)
        self.print("}")
        self.print(self.suffix)
        # trailer = self.grammar.metas.get("trailer", "")
        # if trailer is not None:
        #     self.print(trailer.rstrip("\n"))

    def visit_Rule(self, node: Rule) -> None:
        is_loop = node.is_loop()
        is_gather = node.is_gather()
        rhs = node.flatten()
        if node.left_recursive:
            if node.leader:
                # self.suffix += f"memoizeLeftRecMethod('{node.name}')\n"
                self.print("@memoize_left_rec")
            else:
                # Non-leader rules in a cycle are not memoized,
                # but they must still be logged.
                self.print("@logger")
        else:
            # self.suffix += f"memoizeMethod('{node.name}');\n"
            self.print("@memoize")
        node_type = node.type or "any"
        self.print(f"{node.name}(): {node_type} | null {{")  # -> Optional[{node_type}] {{")
        with self.indent():
            self.print(f"//# {node.name}: {rhs}")
            if node.nullable:
                self.print(f"// # nullable={node.nullable}")
            self.args = {"mark"}
            self.has_cut = False
            orig_file, tmp_file = (
                self.file,
                StringIO(),
            )  # a bit of a hack to get state the args at the top of the file
            self.file = tmp_file
            self.print("mark = this.mark();")
            if is_loop:
                self.args.add("children")
                self.print("children = [];")
            self.visit(rhs, is_loop=is_loop, is_gather=is_gather)
            self.file = orig_file
            self.print(f"let {', '.join(sorted(self.args))};")
            self.print(tmp_file.getvalue())
            tmp_file.close()
            if is_loop:
                if node.name.startswith("_loop0"):
                    self.print("return children;")
                else:
                    self.print("return children.length ? children : null;")
            else:
                self.print("return null;")
        self.print("}")

    def visit_NamedItem(self, node: NamedItem) -> None:
        name, call = self.callmakervisitor.visit(node.item)
        if node.name:
            name = node.name
        if not name:
            self.print(call)
        else:
            if name != "cut":
                name = self.dedupe(name)
            name = fix_reserved(name)
            self.args.add(name)
            self.print(f"({name} = {call})")

    def visit_Rhs(self, node: Rhs, is_loop: bool = False, is_gather: bool = False) -> None:
        if is_loop:
            assert len(node.alts) == 1
        for alt in node.alts:
            self.visit(alt, is_loop=is_loop, is_gather=is_gather)

    def visit_Alt(self, node: Alt, is_loop: bool, is_gather: bool) -> None:
        with self.local_variable_context():
            if self.has_cut:
                self.print("cut = false;")  # TODO: Only if needed.
                self.has_cut = False
            if is_loop:
                self.print("while (")
            else:
                self.print("if (")
            with self.indent():
                first = True
                for item in node.items:
                    if first:
                        first = False
                    else:
                        self.print("&&")
                    self.visit(item)
                    if is_gather:
                        self.print("!== null")

            self.print(") {")
            with self.indent():
                action = node.action
                if not action:
                    if is_gather:
                        assert len(self.local_variable_names) == 2
                        action = f"[{self.local_variable_names[0]}, ...{self.local_variable_names[1]}]"
                    else:
                        action = f"{', '.join(self.local_variable_names)}"
                # action = clean_action(action)
                if is_loop:
                    self.print(f"children.push({action});")
                    self.print("mark = this.mark();")
                else:
                    self.print(f"return {action};")
            self.print("}")
            self.print("this.reset(mark);")
            # Skip remaining alternatives if a cut was reached.
            if self.has_cut:
                self.print("if (cut) return null;")  # TODO: Only if needed.
