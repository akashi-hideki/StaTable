# statable_gui/transition_editor_direct/code_widget.py
"""Code display widget (read-only, ActionDraft support / v2.2).

Version: 2.2.1 (2026-09-19)
  - Fix: Nested group emitted duplicate transition blocks when parent
    and child both declared the same members. The parent now skips
    labels that any descendant declares.

[v2.2 changes]
  - Renders cell_actions (before_transitions / after_transitions).
    Legacy "always" trigger is treated as "before_transitions".
  - Respects early_return per transition (`_handled` guard).
  - §12-5: Recursive group nesting via TransitionRelation.children.
  - Handles entry / exit via State.entry / State.exit lists.
"""

import logging
import re
from typing import List

from PySide6.QtWidgets import QPlainTextEdit
from .draft import ActionDraft, ensure_list

logger = logging.getLogger("transition_editor_direct.code")


_VALID_C_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _to_pascal_case(name: str) -> str:
    """snake_case / camelCase -> PascalCase."""
    if not name:
        return ""
    parts = re.split(r'[_\s]+', name)
    result = ""
    for part in parts:
        if part:
            result += part[0].upper() + part[1:]
    return result


class CodeWidget(QPlainTextEdit):
    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.setReadOnly(True)
        self.update_code()

    def update_code(self):
        logger.debug("CodeWidget.update_code called")
        code = self._generate_code()
        self.draft.generated_code = code
        self.setPlainText(code)
        logger.debug(f"Code updated ({len(code)} chars)")

    # ==================================================================
    # Layer / type resolution
    # ==================================================================
    def _get_layer_name(self) -> str:
        layer = getattr(self.draft, 'layer_name', '') or ''
        if layer:
            return layer

        ns_count = {}
        for item in self.draft.flow_items:
            names = []
            if item.item_type == "transition":
                names.extend(ensure_list(item.params.get('pre_actions', [])))
                names.extend(ensure_list(item.params.get('else_actions', [])))
            elif item.item_type == "function":
                names.append(item.name)
            for n in names:
                if '.' in n:
                    ns = n.split('.', 1)[0]
                    if ns and _VALID_C_IDENTIFIER.match(ns):
                        ns_count[ns] = ns_count.get(ns, 0) + 1

        if ns_count:
            return max(ns_count.items(), key=lambda kv: kv[1])[0]
        return ''

    def _context_type(self) -> str:
        layer = self._get_layer_name()
        return f"TransitionContext_{layer}_t" if layer else "TransitionContext_t"

    # ==================================================================
    # Reference -> RoleFunc name
    # ==================================================================
    def _role_func_name(self, ref: str) -> str:
        """Convert reference string to RoleFunc_<Namespace>_<PascalName>."""
        if not ref:
            return ""
        name = ref.strip()
        if not name:
            return ""

        if '(' in name:
            name = name.split('(', 1)[0].strip()

        if name.startswith("RoleFunc_"):
            rest = name[len("RoleFunc_"):]
            rest = rest.replace('.', '_')
            if _VALID_C_IDENTIFIER.match(rest):
                return f"RoleFunc_{rest}"
            return ""

        if '.' in name:
            ns, base = name.split('.', 1)
            if not (_VALID_C_IDENTIFIER.match(ns)
                    and _VALID_C_IDENTIFIER.match(base)):
                return ""
            pascal = _to_pascal_case(base)
            return f"RoleFunc_{ns}_{pascal}"

        if not _VALID_C_IDENTIFIER.match(name):
            logger.warning(
                f"_role_func_name: reject invalid identifier: {ref!r}")
            return ""
        pascal = _to_pascal_case(name)
        return f"RoleFunc_{pascal}"

    def _call_stmt(self, ref: str) -> str:
        fn = self._role_func_name(ref)
        if not fn:
            return f"/* Invalid reference: {ref} */"
        return f"{fn}(transition, ctx);"

    # ==================================================================
    # Code generation
    # ==================================================================
    def _generate_code(self) -> str:
        logger.debug("=== _generate_code START ===")
        lines = []

        context_type = self._context_type()

        # ---- System globals ----
        for g in self.draft.system_globals:
            lines.append(f"{g.type} {g.name} = {g.initial_value};")
        if self.draft.system_globals:
            lines.append("")

        # ---- Collect role function prototypes ----
        proto_names = set()
        for item in self.draft.flow_items:
            if item.item_type == "transition":
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                for p in pre_actions:
                    proto_names.add(p)
                for ea in else_actions:
                    proto_names.add(ea)
            elif item.item_type == "function":
                proto_names.add(item.name)

        for a in self.draft.cell_actions:
            if a.role_function:
                proto_names.add(a.role_function)

        if proto_names:
            for ref in sorted(proto_names):
                func_name = self._role_func_name(ref)
                if not func_name:
                    lines.append(
                        f"/* Undefined reference (invalid identifier): {ref} */")
                    continue
                lines.append(
                    f"int {func_name}("
                    f"const {context_type} *transition, "
                    f"SystemContext_t *ctx);"
                )
            lines.append("")

        # ---- Body ----
        needs_handled = any(
            item.params.get('early_return', False)
            for item in self.draft.flow_items
            if item.item_type == "transition"
        )

        # ---- Cell actions (pre): before_transitions (+ legacy always) ----
        pre_actions_for_cell = [
            a for a in self.draft.cell_actions
            if a.trigger in ("before_transitions", "always")
        ]
        if pre_actions_for_cell:
            lines.append("/* ===== Cell actions (before_transitions) ===== */")
            for a in pre_actions_for_cell:
                lines.append("    " + self._call_stmt(a.role_function))
            lines.append("")

        # ---- Transitions (v2.2 §12-5 recursive) ----
        transitions = [it for it in self.draft.flow_items
                       if it.item_type == "transition"]
        if transitions:
            if needs_handled:
                lines.append("bool _handled = false;")
                lines.append("")

            # Build by_label map
            by_label = {}
            for it in transitions:
                lbl = it.params.get('label', '') or ''
                if lbl:
                    by_label[lbl] = it

            # Collect mentioned labels
            mentioned = set()

            def collect(rel):
                for m in (rel.members or []):
                    mentioned.add(m)
                for c in (getattr(rel, 'children', None) or []):
                    collect(c)

            for rel in self.draft.cell_relations:
                collect(rel)

            # Emit relations in order
            for rel in self.draft.cell_relations:
                self._emit_relation_inline(
                    rel, by_label, lines, indent_level=1)

            # Emit un-mentioned transitions
            for it in transitions:
                lbl = it.params.get('label', '') or ''
                if lbl and lbl in mentioned:
                    continue
                self._emit_transition_item(it, lines, indent=1)

        # ---- Cell actions (post): after_transitions ----
        after_actions = [a for a in self.draft.cell_actions
                         if a.trigger == "after_transitions"]
        if after_actions:
            lines.append("/* ===== Cell actions (after_transitions) ===== */")
            for a in after_actions:
                lines.append("    " + self._call_stmt(a.role_function))
            lines.append("")

        generated = "\n".join(lines).rstrip()
        logger.debug("=== Generated Code ===")
        logger.debug(generated)
        logger.debug("=== _generate_code END ===")
        return generated

    # ==================================================================
    # §12-5: Recursive relation emission
    # ==================================================================
    def _collect_child_labels_inline(self, rel) -> set:
        """Recursively collect all labels mentioned in descendants of rel.

        [v2.2.1 fix]
          Used to avoid emitting the same transition twice when a parent
          and its child both declare the same members.
        """
        labels = set()
        for child in (getattr(rel, 'children', None) or []):
            labels.update(getattr(child, 'members', None) or [])
            labels.update(self._collect_child_labels_inline(child))
        return labels

    def _emit_relation_inline(self, rel, by_label, lines, indent_level=1):
        """Recursively emit one relation into `lines`.

        [v2.2.1 fix]
          Labels handled by child relations are not emitted by the
          parent, avoiding duplicate transition blocks.
        """
        pad = "    " * indent_level
        shared_cond = (getattr(rel, 'shared_condition', '') or '').strip()
        has_cond = bool(shared_cond)

        if has_cond:
            lines.append("/* ===== Group (shared_condition) ===== */")
            lines.append(f"{pad}if ({shared_cond}) {{")
            inner_indent = indent_level + 1
        else:
            inner_indent = indent_level

        # v2.2.1: labels handled by descendants are skipped here
        child_labels = self._collect_child_labels_inline(rel)

        # Members (skip those delegated to children)
        for label in (getattr(rel, 'members', None) or []):
            if label in child_labels:
                continue
            it = by_label.get(label)
            if it is None:
                continue
            self._emit_transition_item(it, lines, indent=inner_indent)

        # Children (recursively)
        for child in (getattr(rel, 'children', None) or []):
            self._emit_relation_inline(child, by_label, lines,
                                       indent_level=inner_indent)

        if has_cond:
            lines.append(f"{pad}}}")

    def _emit_transition_item(self, item, lines, indent=1):
        """Emit one transition item into `lines` at the given indent."""
        params = item.params
        pad = "    " * indent
        label = params.get('label', '') or ''
        cond = params.get('condition', '')
        target = params.get('target', '') or self.draft.default_target
        pre_actions = ensure_list(params.get('pre_actions', []))
        else_actions = ensure_list(params.get('else_actions', []))
        has_else = params.get('has_else', True)
        else_target = (params.get('else_target', '')
                       or self.draft.default_target)
        early_return = params.get('early_return', False)

        cond_expr = cond if cond else "1"
        mode = "Commit" if early_return else "Tentative"
        lines.append(f"{pad}/* ===== Transition[{label}] ({mode}) ===== */")

        if early_return:
            lines.append(f"{pad}if (!_handled && {cond_expr}) {{")
        else:
            lines.append(f"{pad}if ({cond_expr}) {{")

        for p in pre_actions:
            lines.append(f"{pad}    " + self._call_stmt(p))
        if target:
            lines.append(f"{pad}    next_state = {target};")
        if early_return:
            lines.append(f"{pad}    _handled = true;")

        if has_else and (else_target or else_actions):
            if early_return:
                lines.append(
                    f"{pad}}} else if (!_handled && !({cond_expr})) {{")
            else:
                lines.append(f"{pad}}} else {{")
            for ea in else_actions:
                lines.append(f"{pad}    " + self._call_stmt(ea))
            if else_target:
                lines.append(f"{pad}    next_state = {else_target};")
            if early_return:
                lines.append(f"{pad}    _handled = true;")

        lines.append(f"{pad}}}")
        lines.append("")