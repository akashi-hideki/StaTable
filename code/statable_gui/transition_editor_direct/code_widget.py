# statable_gui/transition_editor_direct/code_widget.py
"""\nCode display widget (read-only, ActionDraft support)\n- Enhanced debug logging\n- Detailed output of each FlowItem's processing\n\n[v1.5 fix]\n  - Removed the old form `void RoleFunc_xxx(ctx, transition)`\n  - Unified to a form consistent with real file generation (role_function_generator.py):\n    * Return type: int (per role_function_generator convention)\n    * Function name: RoleFunc_<Namespace>_<PascalName> (dots replaced with _)\n    * Arg order: (const TransitionContext_<Layer>_t *transition, SystemContext_t *ctx)\n  - Split Namespace and Name from qualified_name ('Driver.Init')\n"""

import logging
import re

from PySide6.QtWidgets import QPlainTextEdit
from .draft import ActionDraft, ensure_list

logger = logging.getLogger("transition_editor_direct.code")


# A valid C identifier form (rejects e.g. `retry_count++`)
_VALID_C_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _to_pascal_case(name: str) -> str:
    """snake_case / camelCase → PascalCase"""
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
    # Resolve layer name and type name
    # ==================================================================
    def _get_layer_name(self) -> str:
        """\n        Infer layer name from ActionDraft\n\n        - Cannot be inferred from draft.role_func_map etc.,\n          so collect the Namespace part of function names\n          (e.g., 'Middleware' from 'Middleware.HandleErr')\n          and use the most frequent value\n        - If undeterminable, empty string (no layer)\n        """
        # 1. If ActionDraft has a layer_name attribute, use it (future extension)
        layer = getattr(self.draft, 'layer_name', '') or ''
        if layer:
            return layer

        #2. Count namespaces of referenced functions
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
    # Reference name -> RoleFunc function name
    # ==================================================================
    def _role_func_name(self, ref: str) -> str:
        """\n        Convert reference string to RoleFunc_<Namespace>_<PascalName>\n\n        Input examples:\n          'Middleware.HandleErr'  -> 'RoleFunc_Middleware_HandleErr'\n          'Driver.Init'           -> 'RoleFunc_Driver_Init'\n          'HandleError'           -> 'RoleFunc_HandleError'\n          'RoleFunc_Xxx'          -> 'RoleFunc_Xxx' (already prefixed)\n          'retry_count++'         -> '' (invalid identifier)\n        """
        if not ref:
            return ""
        name = ref.strip()
        if not name:
            return ""

        # Strip argument part
        if '(' in name:
            name = name.split('(', 1)[0].strip()

        # If it already starts with RoleFunc_, keep as-is
        if name.startswith("RoleFunc_"):
            rest = name[len("RoleFunc_"):]
            rest = rest.replace('.', '_')
            if _VALID_C_IDENTIFIER.match(rest):
                return f"RoleFunc_{rest}"
            return ""

        # Namespace.Name → Namespace_Name
        if '.' in name:
            ns, base = name.split('.', 1)
            if not (_VALID_C_IDENTIFIER.match(ns)
                    and _VALID_C_IDENTIFIER.match(base)):
                return ""
            pascal = _to_pascal_case(base)
            return f"RoleFunc_{ns}_{pascal}"

        # Bare name
        if not _VALID_C_IDENTIFIER.match(name):
            logger.warning(
                f"_role_func_name: reject invalid identifier: {ref!r}"
            )
            return ""
        pascal = _to_pascal_case(name)
        return f"RoleFunc_{pascal}"

    # ==================================================================
    # Code generation
    # ==================================================================
    def _generate_code(self) -> str:
        logger.debug("=== _generate_code START ===")
        lines = []

        context_type = self._context_type()

        #System global definitions (if any)
        for g in self.draft.system_globals:
            lines.append(f"{g.type} {g.name} = {g.initial_value};")
        if self.draft.system_globals:
            lines.append("")

        # Collect role function prototypes (dedupe)
        proto_names = set()
        for item in self.draft.flow_items:
            logger.debug(
                f"Processing flow_item for prototypes: "
                f"type={item.item_type}, name={item.name}"
            )
            if item.item_type == "transition":
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                for p in pre_actions:
                    proto_names.add(p)
                for ea in else_actions:
                    proto_names.add(ea)
            elif item.item_type == "function":
                proto_names.add(item.name)

        if proto_names:
            # Output matching real file generation
            for ref in sorted(proto_names):
                func_name = self._role_func_name(ref)
                if not func_name:
                    lines.append(
                        f"/* 未定義参照（無効な識別子）: {ref} */"
                    )
                    continue
                lines.append(
                    f"int {func_name}("
                    f"const {context_type} *transition, "
                    f"SystemContext_t *ctx);"
                )
            lines.append("")

        # Body
        for item in self.draft.flow_items:
            logger.debug(
                f"Processing flow_item for code: "
                f"type={item.item_type}, name={item.name}, params={item.params}"
            )
            if item.item_type == "transition":
                cond = item.params.get('condition', '')
                target = item.params.get('target', '')
                if not target:
                    target = self.draft.default_target
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')
                if not else_target:
                    else_target = self.draft.default_target

                if cond:
                    lines.append(f"if ({cond}) {{")
                    for p in pre_actions:
                        func_name = self._role_func_name(p)
                        if func_name:
                            lines.append(
                                f"    {func_name}(transition, ctx);"
                            )
                        else:
                            lines.append(
                                f"    /* 不正な参照: {p} */"
                            )
                    if target:
                        lines.append(f"    next_state = {target};")
                    else:
                        lines.append("    // TargetNot set")
                    lines.append("}")
                    if has_else:
                        lines.append("else {")
                        for ea in else_actions:
                            func_name = self._role_func_name(ea)
                            if func_name:
                                lines.append(
                                    f"    {func_name}(transition, ctx);"
                                )
                            else:
                                lines.append(
                                    f"    /* 不正な参照: {ea} */"
                                )
                        if else_target:
                            lines.append(f"    next_state = {else_target};")
                        else:
                            lines.append("    // else target (not set)")
                        lines.append("}")
                else:
                    if target:
                        lines.append(f"next_state = {target};")
                    else:
                        lines.append("// TargetNot set")

            elif item.item_type == "function":
                func_name = self._role_func_name(item.name)
                if func_name:
                    lines.append(f"{func_name}(transition, ctx);")
                else:
                    lines.append(f"/* 不正な参照: {item.name} */")

        # Debug log
        generated = "\n".join(lines)
        logger.debug("=== Generated Code ===")
        logger.debug(generated)
        logger.debug("=== _generate_code END ===")
        return generated