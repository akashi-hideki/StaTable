# statable_gui/transition_editor_direct/code_widget.py
"""Code display widget (read-only, ActionDraft support / v2.2).

[v2.2 changes]
  - Renders cell_actions (always / before_transitions / after_transitions).
  - Respects early_return per transition (`_handled` guard).
  - Renders `group` shared_condition as an outer `if`.
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

        # System globals
        for g in self.draft.system_globals:
            lines.append(f"{g.type} {g.name} = {g.initial_value};")
        if self.draft.system_globals:
            lines.append("")

        # Collect role function prototypes
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

        # Cell actions also need prototypes
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
        # Determine whether we need _handled
        needs_handled = any(
            item.params.get('early_return', False)
            for item in self.draft.flow_items
            if item.item_type == "transition"
        )

        # Cell actions (always / before_transitions)
        for trigger in ("always", "before_transitions"):
            trigger_actions = [a for a in self.draft.cell_actions
                               if a.trigger == trigger]
            if trigger_actions:
                lines.append(f"/* ===== Cell actions ({trigger}) ===== */")
                for a in trigger_actions:
                    lines.append("    " + self._call_stmt(a.role_function))
                lines.append("")

        # Transitions
        transitions = [it for it in self.draft.flow_items
                       if it.item_type == "transition"]
        if transitions:
            # Open _handled declaration
            if needs_handled:
                lines.append("bool _handled = false;")
                lines.append("")

            # Group map
            group_map = {}
            for rel in self.draft.cell_relations:
                if rel.kind == "group" and rel.shared_condition:
                    for lbl in rel.members:
                        group_map[lbl] = rel.shared_condition

            open_group_cond = None
            for idx, item in enumerate(transitions):
                params = item.params
                label = params.get('label', '') or f"T{idx + 1}"
                cond = params.get('condition', '')
                target = params.get('target', '') or self.draft.default_target
                pre_actions = ensure_list(params.get('pre_actions', []))
                else_actions = ensure_list(params.get('else_actions', []))
                has_else = params.get('has_else', True)
                else_target = params.get('else_target', '') or self.draft.default_target
                early_return = params.get('early_return', False)

                sc = group_map.get(label)
                # Open group
                if sc and sc != open_group_cond:
                    lines.append(
                        f"/* ===== Group (shared_condition) ===== */")
                    lines.append(f"if ({sc}) {{")
                    open_group_cond = sc
                # Close previous group if changed
                elif open_group_cond and sc != open_group_cond:
                    lines.append("}")
                    open_group_cond = None

                indent = "    " if open_group_cond else ""
                cond_expr = cond if cond else "1"
                mode = "Commit" if early_return else "Tentative"
                lines.append(f"{indent}/* ===== Transition[{label}] ({mode}) ===== */")

                # Condition
                if early_return:
                    lines.append(f"{indent}if (!_handled && {cond_expr}) {{")
                else:
                    lines.append(f"{indent}if ({cond_expr}) {{")

                for p in pre_actions:
                    lines.append(f"{indent}    " + self._call_stmt(p))

                if target:
                    lines.append(f"{indent}    next_state = {target};")

                if early_return:
                    lines.append(f"{indent}    _handled = true;")

                # else branch
                if has_else and (else_target or else_actions):
                    if early_return:
                        lines.append(
                            f"{indent}}} else if (!_handled && !({cond_expr})) {{")
                    else:
                        lines.append(f"{indent}}} else {{")
                    for ea in else_actions:
                        lines.append(f"{indent}    " + self._call_stmt(ea))
                    if else_target:
                        lines.append(f"{indent}    next_state = {else_target};")
                    if early_return:
                        lines.append(f"{indent}    _handled = true;")

                lines.append(f"{indent}}}")
                lines.append("")

            # Close group
            if open_group_cond:
                lines.append("}")
                lines.append("")

        # Cell actions (after_transitions)
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