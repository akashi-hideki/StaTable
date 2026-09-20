# StaTable Class Index

Roots: statable, statable_gui, statable_gui/libcntrl, statable_gui/transition_editor_direct, codegen

## `codegen\__init__.py`
- (no classes)

## `codegen\c_code_generator.py`
- **CCodeGenerator** (L70) bases=[]
    - `__init__`
    - `_log_debug`
    - `get_config`
    - `set_config`
    - `update_config`
    - `reset_config`
    - `_get_states_list`
    - `_get_events_list`
    - `_get_role_functions_list`
    - `_get_layer_name`
    - `_get_initial_state`
    - `_generate_section_header`
    - `_generate_file_header`
    - `_generate_include_guard_start`
    - `_generate_include_guard_end`
    - `_generate_include_section`
    - `_layer_filename`
    - `_layer_suffix`
    - `_normalize_layers`
    - `_setup_layer_generators`
    - `_resolve_output_path`
    - `_resolve_super_include_path`
    - `_resolve_path_flat`
    - `_resolve_path_by_type`
    - `_resolve_path_by_layer`
    - `_run_steps`
    - `_run_steps_multi`
    - `_step_file_header`
    - `_step_blank`
    - `_step_guard_start`
    - `_step_guard_end`
    - `_step_include_section`
    - `_step_section_header`
    - `_step_enums`
    - `_step_enums_common`
    - `_step_layer_transition_context`
    - `_step_common_function_decls`
    - `_step_custom_types`
    - `_step_struct`
    - `_step_var_macros`
    - `_step_state_machine_decl`
    - `_step_cell_prototypes`
    - `_step_transition_table`
    - `_step_cell_functions`
    - `_step_process_func`
    - `_step_get_next_event`
    - `_step_role_decls`
    - `_step_role_impls`
    - `_step_init_func`
    - `_step_event_queues`
    - `_step_interrupts`
    - `_step_timer_struct`
    - `_step_timer_init`
    - `_step_timer_update`
    - `_step_osal_header`
    - `_step_osal_source`
    - `_step_super_include_header`
    - `_step_super_include_guard_start`
    - `_step_super_include_guard_end`
    - `_step_super_include_common`
    - `_step_super_include_layer`
    - `_step_super_include_project`
    - `_step_super_include_extern_vars`
    - `_step_super_include_extern_funcs`
    - `_step_super_include_external`
    - `_step_super_include_user`
    - `_step_super_loop_header`
    - `_step_super_loop_include`
    - `_step_super_loop_context_var`
    - `_step_super_loop_state_var`
    - `_step_super_loop_init_func`
    - `_step_super_loop_run_func`
    - `_generate_types_common_header`
    - `_generate_types_header`
    - `_generate_transitions_header`
    - `_generate_transitions_source`
    - `_generate_role_functions_header`
    - `_generate_role_functions_source`
    - `_generate_init_source`
    - `_generate_event_queue_source`
    - `_generate_interrupt_source`
    - `_generate_timer_source`
    - `_generate_osal_header`
    - `_generate_osal_source`
    - `_generate_super_include`
    - `_generate_super_loop`
    - `generate_all`
    - `generate_file`
    - `generate_all_layers`
    - `_generate_all_by_layer`
    - `save_generated_code`
    - `save_generated_code_with_merge`
    - `get_merge_summary`
    - `get_generated_file_list`

## `codegen\code_merger.py`
- **CodeMerger** (L28) bases=[]
    - `__init__`
    - `_log_debug`
    - `extract_file_user_code`
    - `extract_func_user_code`
    - `extract_all_func_user_codes`
    - `extract_file_tail_user_code`
    - `inject_file_user_code`
    - `inject_func_user_code`
    - `inject_file_tail_user_code`
    - `merge_file`
    - `merge_all_files`
    - `has_user_code`
    - `has_func_user_code`
    - `get_user_code_summary`

## `codegen\code_templates.py`
- **CodeTemplates** (L21) bases=[]

## `codegen\config.py`
- **CodeGenerationConfig** (L12) bases=[]
    - `to_dict`
    - `from_dict`
- **ConfigManager** (L115) bases=[]
    - `__init__`
    - `get_config`
    - `set_config`
    - `update`
    - `reset`
    - `get_available_styles`
    - `get_available_table_types`
    - `get_available_os_types`
    - `get_available_folder_structures`

## `codegen\enum_generator.py`
- **CEnumGenerator** (L31) bases=[]
    - `__init__`
    - `set_layer`
    - `_log_debug`
    - `_state_value_name`
    - `_event_value_name`
    - `_flag_value_name`
    - `_state_type_name`
    - `_event_type_name`
    - `_flag_type_name`
    - `_state_max_name`
    - `_event_max_name`
    - `_flag_max_name`
    - `_generate_state_comment`
    - `_generate_event_comment`
    - `_generate_flag_comment`
    - `_generate_enum_values`
    - `generate_state_enum`
    - `generate_event_enum`
    - `generate_flag_enum`
    - `generate_all_enums`
    - `generate_bit_mask_enum`
    - `generate_enum`

## `codegen\event_queue_generator.py`
- **EventQueueGenerator** (L25) bases=[]
    - `__init__`
    - `_log_debug`
    - `_generate_struct_name`
    - `_generate_func_prefix`
    - `_execute_struct_comment`
    - `_execute_struct_start`
    - `_execute_members`
    - `_execute_struct_end`
    - `_execute_enqueue_comment`
    - `_execute_enqueue_signature`
    - `_execute_dequeue_comment`
    - `_execute_dequeue_signature`
    - `_execute_open`
    - `_execute_close`
    - `_execute_null_check`
    - `_execute_full_check`
    - `_execute_empty_check`
    - `_execute_enqueue_body`
    - `_execute_dequeue_body`
    - `generate_struct`
    - `generate_enqueue_function`
    - `generate_dequeue_function`
    - `generate_all_code`
    - `generate_all_structs`
    - `generate_all_functions`
    - `generate_all`

## `codegen\interrupt_generator.py`
- **InterruptGenerator** (L37) bases=[]
    - `__init__`
    - `set_layer`
    - `_log_debug`
    - `_get_isr_function_name`
    - `_get_marker_name`
    - `_get_handler_display_name`
    - `_parse_action`
    - `_parse_action_with_semicolon`
    - `extract_used_symbols`
    - `update_handler_symbols`
    - `_execute_comment_step`
    - `_execute_signature_step`
    - `_execute_open_step`
    - `_execute_context_step`
    - `_execute_enter_log_step`
    - `_execute_actions_step`
    - `_execute_user_section_step`
    - `_execute_exit_log_step`
    - `_execute_close_step`
    - `generate_isr`
    - `generate_all_isrs`

## `codegen\naming_convention.py`
- **CNamingConvention** (L23) bases=[]
    - `__init__`
    - `to_snake_case`
    - `to_upper_snake`
    - `to_lower_snake`
    - `to_camel_case`
    - `to_pascal_case`
    - `sanitize_identifier`
    - `create_identifier`
    - `create_type_name`
    - `create_enum_value`
    - `create_function_name`
    - `create_variable_name`
    - `create_macro_name`

## `codegen\osal_generator.py`
- **OSALGenerator** (L29) bases=[]
    - `__init__`
    - `_log_debug`
    - `_execute_file_comment`
    - `_execute_include_guard_start`
    - `_execute_includes`
    - `_execute_type_defs`
    - `_execute_mutex_decls`
    - `_execute_semaphore_decls`
    - `_execute_queue_decls`
    - `_execute_critical_decls`
    - `_execute_include_guard_end`
    - `_execute_mutex_impl`
    - `_execute_semaphore_impl`
    - `_execute_queue_impl`
    - `_execute_critical_impl`
    - `generate_header`
    - `generate_source`
    - `generate_all`
    - `get_available_os_types`

## `codegen\role_function_generator.py`
- **RoleFuncCallSite** (L80) bases=[]
    - `__init__`
    - `key`
    - `__repr__`
- **RoleFunctionGenerator** (L99) bases=[]
    - `__init__`
    - `set_layer`
    - `_log_debug`
    - `_resolve_name_and_namespace`
    - `_generate_function_name`
    - `_get_marker_name`
    - `_get_short_name`
    - `_context_type`
    - `_state_type`
    - `_event_type`
    - `_state_enum`
    - `_event_enum`
    - `_state_max`
    - `_event_none`
    - `_entry_struct_type`
    - `_dedupe_by_name`
    - `_resolve_comment_title`
    - `_normalize_func_ref`
    - `_extract_func_names_from_condition`
    - `_collect_call_sites`
    - `_get_call_sites_for_func`
    - `_format_call_sites_comment`
    - `_should_emit_implementation`
    - `_should_declare_here`
    - `generate_none_define`
    - `generate_entry_struct`
    - `generate_transition_id_prototype`
    - `generate_transition_id_function`
    - `generate_call_sites_table`
    - `generate_tail_user_section`
    - `_format_var_comment`
    - `_generate_local_transition_members`
    - `_generate_local_transition_id`
    - `_generate_local_data_pointers`
    - `_has_local_data_pointers`
    - `_generate_local_retvar`
    - `generate_declaration`
    - `generate_implementation`
    - `generate_call`
    - `generate_all_declarations`
    - `generate_all_implementations`
    - `_collect_args`

## `codegen\sample_data.py`
- **SampleDataGenerator** (L28) bases=[]
    - `__init__`
    - `create_sample_state_machine`
    - `create_sample_global_defs`
    - `get_sample_data`

## `codegen\struct_generator.py`
- **CStructGenerator** (L43) bases=[]
    - `__init__`
    - `set_layer`
    - `_log_debug`
    - `_detect_member_type`
    - `_generate_member`
    - `_generate_custom_type`
    - `_generate_system_data`
    - `_generate_event_flags`
    - `_generate_system_context`
    - `generate_common_transition_context`
    - `generate_layer_transition_context`
    - `generate_pending_event_macros`
    - `generate_all_structs`
    - `generate_all`
    - `generate_struct`

## `codegen\timer_generator.py`
- **TimerGenerator** (L40) bases=[]
    - `__init__`
    - `_log_debug`
    - `_get_all_timers`
    - `_get_all_derived_timers`
    - `_execute_struct_comment`
    - `_execute_struct_start`
    - `_execute_members`
    - `_execute_struct_end`
    - `_execute_init_comment`
    - `_execute_init_signature`
    - `_execute_open`
    - `_execute_close`
    - `_execute_null_check`
    - `_execute_entry_log`
    - `_execute_init_base_timers`
    - `_execute_init_derived_timers`
    - `_execute_exit_log`
    - `_execute_update_comment`
    - `_execute_update_signature`
    - `_execute_update_derived_timers`
    - `generate_struct`
    - `generate_init_function`
    - `generate_update_function`
    - `generate_all`

## `codegen\transition_generator.py`
- **TransitionGenerator** (L56) bases=[]
    - `__init__`
    - `set_layer`
    - `_log_debug`
    - `_state_enum`
    - `_event_enum`
    - `_state_type`
    - `_event_type`
    - `_context_type`
    - `_func_type`
    - `_table_name`
    - `_state_max`
    - `_event_max`
    - `_cell_func_name`
    - `_resolve_role_func_name`
    - `_role_func_call_expr`
    - `_role_func_call_action`
    - `_role_func_call_bare`
    - `_role_func_call`
    - `_build_exit_call`
    - `_build_entry_call`
    - `_build_transition_block`
    - `_build_transitions_block`
    - `_collect_child_labels`
    - `_emit_relation`
    - `_indent_block`
    - `generate_transition_cell_functions`
    - `_build_cell_function`
    - `generate_transition_cell_prototypes`
    - `generate_transition_table`
    - `_generate_table_array`
    - `_generate_table_switch`
    - `_generate_table_dictionary`
    - `generate_transition_table_header`
    - `generate_function_dictionary`
    - `generate_process_function`
    - `_generate_process_table_driven`
    - `_generate_process_switch_case`
    - `generate_get_next_event_function`
    - `generate_all`
    - `generate_all_transitions`

## `codegen\type_mapper.py`
- **CTypeMapper** (L18) bases=[]
    - `__init__`
    - `map_type`
    - `get_type_category`
    - `get_required_headers`

## `codegen\validate\__init__.py`
- (no classes)

## `codegen\validate\change_actions.py`
- **ChangeActionType** (L18) bases=['Enum']
- **ChangeRequest** (L47) bases=[]
    - `to_dict`
    - `from_dict`
    - `__str__`

## `codegen\validate\change_applier.py`
- **ChangeApplier** (L26) bases=[]
    - `__init__`
    - `apply`
    - `apply_all`
    - `_set_initial`
    - `_add_transition`
    - `_add_state`
    - `_add_event`
    - `_remove_transition`
    - `_update_transition`
    - `_add_role_function`
    - `_remove_role_function`
    - `_add_variable`
    - `_add_flag`
    - `_add_cell`
    - `_remove_cell`
    - `_add_action_step`
    - `_remove_action_step`
    - `_add_transition_relation`
    - `_remove_transition_relation`
    - `_set_early_return`

## `codegen\validate\clipboard_manager.py`
- **ClipboardManager** (L12) bases=[]
    - `copy_to_clipboard`
    - `get_from_clipboard`

## `codegen\validate\data\__init__.py`
- (no classes)

## `codegen\validate\data\action_definitions.py`
- (no classes)

## `codegen\validate\data\keywords.py`
- (no classes)

## `codegen\validate\data\prompt_templates.py`
- (no classes)

## `codegen\validate\data\validation_rules.py`
- (no classes)

## `codegen\validate\items\__init__.py`
- (no classes)

## `codegen\validate\items\base_validator.py`
- **BaseValidator** (L13) bases=[]
    - `validate`

## `codegen\validate\items\cell_validator.py`
- **CellValidator** (L27) bases=['BaseValidator']
    - `__init__`
    - `_severity`
    - `_make_issue`
    - `_iter_cells`
    - `_loc`
    - `_rule_empty_condition`
    - `_rule_duplicate_label`
    - `_rule_dangling_relation`
    - `_rule_unreachable`
    - `_rule_overlap`
    - `_rule_duplicate_target`
    - `_rule_exclusive_no_return`
    - `_rule_empty_target`

## `codegen\validate\items\custom_type_validator.py`
- **CustomTypeValidator** (L18) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_duplicate_names`
    - `_check_no_members`

## `codegen\validate\items\event_validator.py`
- **EventValidator** (L23) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_unused_events`
    - `_check_events_without_transitions`

## `codegen\validate\items\flag_validator.py`
- **FlagValidator** (L16) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_duplicate_names`
    - `_check_invalid_range`

## `codegen\validate\items\interrupt_validator.py`
- **InterruptValidator** (L16) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_duplicate_names`
    - `_check_undefined_event`

## `codegen\validate\items\queue_validator.py`
- **QueueValidator** (L16) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_invalid_size`
    - `_check_undefined_event`

## `codegen\validate\items\role_function_validator.py`
- **RoleFunctionValidator** (L18) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_no_return_type`
    - `_check_arg_mismatch`
    - `_check_unused_functions`

## `codegen\validate\items\state_validator.py`
- **StateValidator** (L16) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_initial_state`
    - `_check_unreachable_states`
    - `_check_no_transition_states`
    - `_check_duplicate_states`

## `codegen\validate\items\timer_validator.py`
- **TimerValidator** (L18) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_get_all_timer_variables`
    - `_check_duplicate_variables`
    - `_check_invalid_multiplier`

## `codegen\validate\items\transition_validator.py`
- **TransitionValidator** (L23) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_target_undefined`
    - `_check_event_undefined`
    - `_check_source_undefined`
    - `_check_duplicate_transitions`
    - `_check_self_loops`

## `codegen\validate\items\variable_validator.py`
- **VariableValidator** (L16) bases=['BaseValidator']
    - `__init__`
    - `validate`
    - `_create_issue`
    - `_check_duplicate_names`
    - `_check_invalid_type`
    - `_check_invalid_array_size`

## `codegen\validate\logger.py`
- (no classes)

## `codegen\validate\models.py`
- **ValidationSeverity** (L9) bases=['Enum']
    - `from_string`
- **ValidationIssue** (L33) bases=[]
    - `to_dict`
    - `from_dict`
    - `__str__`
- **ValidationResult** (L73) bases=[]
    - `passed`
    - `error_count`
    - `warning_count`
    - `info_count`
    - `get_errors`
    - `get_warnings`
    - `get_infos`
    - `get_by_category`
    - `to_dict`
    - `from_dict`
    - `__str__`
- **ValidationContext** (L126) bases=[]
    - `states`
    - `events`
    - `transitions`
    - `role_functions`
    - `initial_state`
    - `variables`
    - `flags`
    - `event_queues`
    - `interrupts`
    - `custom_types`
    - `timer_base`
    - `extra_timers`

## `codegen\validate\prompt_generator.py`
- **AIPromptGenerator** (L22) bases=[]
    - `__init__`
    - `_format_data`
    - `_format_validation`
    - `generate_diagnosis_prompt`

## `codegen\validate\response_parser.py`
- **AIResponseParser** (L17) bases=[]
    - `__init__`
    - `parse`
    - `parse_json_response`
    - `parse_text_response`
    - `_extract_json`
    - `_extract_with_markers`
    - `_parse_change`
    - `_parse_line`

## `codegen\validate\validation_dialog.py`
- **ValidationDialog** (L31) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_setup_validation_tab`
    - `_setup_prompt_tab`
    - `_setup_response_tab`
    - `_setup_changes_tab`
    - `_run_validation`
    - `_copy_prompt`
    - `_paste_response`
    - `_parse_response`
    - `_apply_changes`

## `codegen\validate\validator.py`
- **CodeGenerationValidator** (L30) bases=[]
    - `__init__`
    - `validate`
    - `validate_category`
    - `get_categories`

## `codegen\variable_generator.py`
- **VariableGenerator** (L49) bases=[]
    - `__init__`
    - `_log_debug`
    - `_detect_variable_type`
    - `_build_context`
    - `_replace_placeholders`
    - `_resolve_value`
    - `_execute_template_step`
    - `_execute_blank_step`
    - `_execute_loop_step`
    - `_generate_data_macro`
    - `_generate_flag_macro`
    - `_generate_access_macro`
    - `_normalize_type_for_init`
    - `_generate_array_init`
    - `_generate_normal_init`
    - `_generate_flag_init`
    - `_generate_init_code`
    - `generate_init_function`
    - `generate_all_macros`
    - `generate_variable`
    - `generate_all`

## `statable\__init__.py`
- (no classes)

## `statable\global_defs.py`
- **StructMemberDef** (L8) bases=[]
    - `__post_init__`
- **CustomTypeDef** (L28) bases=[]
    - `__post_init__`
- **SystemVariable** (L41) bases=[]
    - `__post_init__`
- **EventFlag** (L61) bases=[]
    - `__post_init__`
    - `bit_width`
- **InterruptAction** (L82) bases=[]
- **InterruptHandlerDef** (L89) bases=[]
    - `__post_init__`
- **DevicePlaceholderDef** (L116) bases=[]
    - `__post_init__`
- **TimerDerivedDef** (L128) bases=[]
    - `__post_init__`
- **TimerBaseDef** (L142) bases=[]
    - `__post_init__`
- **EventQueueDef** (L157) bases=[]
    - `__post_init__`
- **GlobalDefinitions** (L174) bases=[]
    - `__init__`
    - `add_timer_variables`
    - `variable_groups`
    - `flag_groups`
    - `custom_type_names`

## `statable\mermaid_gen.py`
- (no classes)

## `statable\model.py`
- **StateType** (L6) bases=['Enum']
- **EventKind** (L16) bases=['Enum']
- **EventDeliveryType** (L23) bases=['Enum']
- **EventSourceLayer** (L30) bases=['Enum']
- **State** (L37) bases=[]
    - `__post_init__`
- **Event** (L68) bases=[]
    - `__post_init__`
- **Transition** (L88) bases=[]
    - `__post_init__`
- **ActionStep** (L125) bases=[]
    - `__post_init__`
- **TransitionRelation** (L149) bases=[]
- **RoleFunction** (L175) bases=[]
    - `__post_init__`
    - `qualified_name`
    - `from_legacy_name`

## `statable\parser.py`
- **ParserNotImplementedError** (L38) bases=['NotImplementedError']

## `statable\sample_data.py`
- (no classes)

## `statable\state_machine.py`
- **StateMachine** (L10) bases=[]
    - `__init__`
    - `add_state`
    - `add_event`
    - `remove_event`
    - `add_transition`
    - `remove_transition`
    - `set_initial`
    - `add_role_function`
    - `remove_role_function`
    - `get_transitions_for_cell`
    - `get_transitions_for_event`
    - `get_actions_for_cell`
    - `set_actions_for_cell`
    - `get_relations_for_cell`
    - `set_relations_for_cell`
    - `get_cell_keys`
    - `remove_cell_metadata`

## `statable\xml_io.py`
- (no classes)

## `statable_gui\__init__.py`
- (no classes)

## `statable_gui\action_edit_dialog.py`
- **ActionEditDialog** (L17) bases=['QDialog']
    - `__init__`
    - `refresh_role_combo`
    - `update_signature_label`
    - `insert_role_function`
    - `add_new_role_function`
    - `insert_symbol`
    - `show_action_context_menu`
    - `register_selected_as_variable`
    - `register_selected_as_flag`
    - `_on_accept`
    - `get_action_text`
    - `get_title`

## `statable_gui\code_generation_dialog.py`
- **WarningCollector** (L67) bases=['logging.Handler']
    - `__init__`
    - `emit`
- **CodeGenerationDialog** (L86) bases=['QDialog']
    - `__init__`
    - `_load_saved_settings`
    - `_save_settings`
    - `_setup_ui`
    - `_load_sample_data_if_needed`
    - `_load_config_to_ui`
    - `_update_info_labels`
    - `_on_output_dir_changed`
    - `_select_output_dir`
    - `_on_style_changed`
    - `_open_settings_dialog`
    - `_show_warnings`
    - `_generate_code`
    - `_update_preview`
    - `_save_code`
    - `_on_close`
    - `get_generated_files`
    - `get_config`

## `statable_gui\code_generation_settings_dialog.py`
- **CodeGenerationSettingsDialog** (L30) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_setup_basic_tab`
    - `_setup_log_tab`
    - `_setup_include_tab`
    - `_setup_output_tab`
    - `_load_config`
    - `_save_config`
    - `_on_ok`
    - `_on_reset`
    - `_select_output_dir`
    - `_on_add_include`
    - `_on_remove_include`
    - `_on_move_include_up`
    - `_on_move_include_down`
    - `get_config`

## `statable_gui\common_widgets.py`
- **TitleEditWidget** (L18) bases=['QWidget']
    - `__init__`
    - `get_title`
    - `set_title`
    - `ensure_title`
- **TypeComboBox** (L48) bases=['QWidget']
    - `__init__`
    - `_refresh_types`
    - `_open_type_manager`
    - `current_text`
    - `set_current_text`
- **GroupComboBox** (L102) bases=['QWidget']
    - `__init__`
    - `_refresh_groups`
    - `_add_group`
    - `current_text`
    - `set_current_text`
- **EventComboBox** (L152) bases=['QComboBox']
    - `__init__`
- **StateComboBox** (L164) bases=['QComboBox']
    - `__init__`
- **GroupAddDialog** (L175) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_group_name`
- **TypeManagerDialog** (L206) bases=['QDialog']
    - `__init__`
    - `_refresh_table`
    - `_get_selected_type`
    - `_on_double_clicked`
    - `_add_type`
    - `_edit_type`
    - `_delete_type`
- **TypeEditDialog** (L309) bases=['QDialog']
    - `__init__`
    - `_refresh_member_table`
    - `_get_selected_member`
    - `_add_member`
    - `_edit_member`
    - `_delete_member`
    - `_on_accept`
    - `get_custom_type`
- **StructMemberEditDialog** (L438) bases=['QDialog']
    - `__init__`
    - `_on_bitfield_toggled`
    - `_on_array_toggled`
    - `_on_accept`
    - `get_member`

## `statable_gui\condition_builder_dialog.py`
- **ConditionBuilderDialog** (L28) bases=['QDialog']
    - `__init__`
    - `_get_states_from_state_machine`
    - `_setup_ui`
    - `set_current_targets`
    - `_populate_tree`
    - `_insert_symbol`
    - `_insert_text`
    - `_insert_number`
    - `_clear_condition`
    - `_update_c_code_view`
    - `_convert_to_c_code`
    - `_add_parentheses_to_comparisons`
    - `_is_fully_parenthesized`
    - `_open_literalization`
    - `get_condition_text`
    - `get_event_name`
    - `get_target_state`
    - `get_else_target_state`
    - `get_c_code_text`
- **LiteralizationDialog** (L373) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_scan_numbers`
    - `_on_accept`
    - `get_updated_condition_text`

## `statable_gui\condition_edit_dialog.py`
- **ConditionEditDialog** (L15) bases=['QDialog']
    - `__init__`
    - `refresh_role_combo`
    - `insert_role_function`
    - `insert_symbol`
    - `_on_accept`
    - `get_condition_text`
    - `get_title`

## `statable_gui\config.py`
- (no classes)

## `statable_gui\dialogs.py`
- **TransitionTable** (L36) bases=['QTableWidget']
    - `__init__`
    - `mouseDoubleClickEvent`
- **TransitionListDialog** (L57) bases=['QDialog']
    - `__init__`
    - `on_cell_double_clicked`
    - `open_condition_builder`
    - `open_dnd_editor_for_row`
    - `open_dnd_editor`
    - `_transition_to_draft`
    - `_draft_to_transition`
    - `_row_to_transition`
    - `_update_row_from_transition`
    - `on_item_changed`
    - `_update_display_title`
    - `add_row`
    - `delete_row`
    - `move_row_up`
    - `move_row_down`
    - `_swap_rows`
    - `_generate_display_title`
    - `_on_accept`
    - `get_transitions`

## `statable_gui\event_definition_dialog.py`
- **DoubleClickTable** (L21) bases=['QTableWidget']
    - `__init__`
    - `mouseDoubleClickEvent`
- **EventEditDialog** (L37) bases=['QDialog']
    - `__init__`
    - `_on_data_check_toggled`
    - `_on_accept`
    - `get_event`
- **EventDefinitionDialog** (L157) bases=['QDialog']
    - `__init__`
    - `refresh_table`
    - `on_item_changed`
    - `_find_event_by_row`
    - `on_double_clicked`
    - `add_event`
    - `delete_event`

## `statable_gui\event_delivery_settings_dialog.py`
- **DoubleClickTable** (L17) bases=['QTableWidget']
    - `__init__`
    - `mouseDoubleClickEvent`
- **EventDeliverySettingsDialog** (L32) bases=['QDialog']
    - `__init__`
    - `_build_table`
    - `_check_isr_usage`
    - `_find_row_by_event_name`
    - `_on_delivery_changed`
    - `_update_converted_column`
    - `_on_accept`
    - `get_auto_convert`

## `statable_gui\event_queue_dialog.py`
- **DoubleClickTable** (L19) bases=['QTableWidget']
    - `__init__`
    - `mouseDoubleClickEvent`
- **EventQueueEditDialog** (L33) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_queue_def`
- **EventQueueDefsDialog** (L126) bases=['QDialog']
    - `__init__`
    - `refresh_table`
    - `_matches`
    - `on_item_changed`
    - `on_double_clicked`
    - `add_queue`
    - `delete_queue`

## `statable_gui\global_defs.py`
- **SystemVariable** (L8) bases=[]
    - `__post_init__`
- **EventFlag** (L24) bases=[]
    - `__post_init__`
    - `bit_width`
- **InterruptAction** (L45) bases=[]
- **InterruptHandlerDef** (L52) bases=[]
    - `__post_init__`
- **DevicePlaceholderDef** (L67) bases=[]
    - `__post_init__`
- **TimerDerivedDef** (L79) bases=[]
    - `__post_init__`
- **TimerBaseDef** (L93) bases=[]
    - `__post_init__`
- **EventQueueDef** (L108) bases=[]
    - `__post_init__`
- **GlobalDefinitions** (L125) bases=[]
    - `__init__`
    - `add_timer_variables`
    - `variable_groups`
    - `flag_groups`

## `statable_gui\global_defs_dialog.py`
- **ComboBoxDelegate** (L20) bases=['QStyledItemDelegate']
    - `__init__`
    - `set_items`
    - `createEditor`
    - `setEditorData`
    - `setModelData`
- **InsertableTable** (L44) bases=['QTableWidget']
    - `__init__`
    - `keyPressEvent`
    - `_show_context_menu`
- **ReadOnlyDelegate** (L65) bases=['QStyledItemDelegate']
    - `createEditor`
- **VariableEditDialog** (L70) bases=['QDialog']
    - `__init__`
    - `_on_array_toggled`
    - `_on_accept`
    - `get_variable`
- **FlagEditDialog** (L146) bases=['QDialog']
    - `__init__`
    - `update_bit_width_label`
    - `_on_accept`
    - `get_flag`
- **BulkVariableDialog** (L217) bases=['QDialog']
    - `__init__`
    - `_type_list`
    - `set_variables`
    - `add_row`
    - `add_empty_row`
    - `delete_row`
    - `_on_accept`
    - `get_variables`
- **BulkFlagDialog** (L337) bases=['QDialog']
    - `__init__`
    - `set_flags`
    - `add_row`
    - `add_empty_row`
    - `delete_row`
    - `on_item_changed`
    - `update_bit_width`
    - `_on_accept`
    - `get_flags`
- **GlobalDefinitionsDialog** (L469) bases=['QDialog']
    - `__init__`
    - `_create_variable_tab`
    - `_create_flag_tab`
    - `_type_list`
    - `on_search_changed`
    - `_matches`
    - `refresh_variables`
    - `on_variable_item_changed`
    - `_read_variable_row`
    - `add_empty_variable_row`
    - `delete_variable`
    - `bulk_variables`
    - `refresh_flags`
    - `on_flag_item_changed`
    - `_read_flag_row`
    - `add_empty_flag_row`
    - `delete_flag`
    - `bulk_flags`

## `statable_gui\interrupt_handler_edit_dialog.py`
- **DoubleClickTable** (L29) bases=['QTableWidget']
    - `__init__`
    - `mouseDoubleClickEvent`
- **InterruptEditDialog** (L47) bases=['QDialog']
    - `__init__`
    - `add_action_row`
    - `delete_action_row`
    - `on_action_double_clicked`
    - `_on_accept`
    - `get_interrupt`
- **DevicePlaceholderEditDialog** (L255) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_placeholder`
- **TimerBaseEditDialog** (L298) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_timer_base`
- **TimerDerivedEditDialog** (L354) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_derived`
- **InterruptHandlerEditDialog** (L410) bases=['QDialog']
    - `__init__`
    - `_create_interrupt_tab`
    - `refresh_interrupt_table`
    - `on_interrupt_double_clicked`
    - `add_interrupt`
    - `delete_interrupt`
    - `_create_placeholder_tab`
    - `refresh_placeholder_table`
    - `on_placeholder_double_clicked`
    - `add_placeholder`
    - `delete_placeholder`
    - `_create_timer_tab`
    - `refresh_timer_tabs`
    - `_create_timer_base_tab`
    - `_refresh_derived_table`
    - `_on_timer_title_changed`
    - `_on_timer_var_changed`
    - `_on_timer_unit_changed`
    - `_on_timer_type_changed`
    - `_on_timer_interrupt_changed`
    - `add_timer_base`
    - `edit_timer_base`
    - `close_timer_tab`
    - `rename_timer_tab`
    - `on_derived_double_clicked`
    - `add_derived`
    - `delete_derived`

## `statable_gui\layer_settings_dialog.py`
- **LayerSettingsDialog** (L19) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_load_layers`
    - `_on_ok`
    - `apply_settings`

## `statable_gui\libcntrl\__init__.py`
- (no classes)

## `statable_gui\libcntrl\condition_library.py`
- **ConditionTemplate** (L9) bases=[]
    - `to_dict`
    - `from_dict`
- **ConditionLibrary** (L31) bases=[]
    - `__init__`
    - `add`
    - `remove`
    - `get`
    - `list_all`
    - `to_dict`
    - `from_dict`

## `statable_gui\libcntrl\literal_library.py`
- **LiteralDefinition** (L9) bases=[]
    - `to_dict`
    - `from_dict`
- **LiteralLibrary** (L34) bases=[]
    - `__init__`
    - `add`
    - `remove`
    - `get`
    - `list_all`
    - `to_dict`
    - `from_dict`

## `statable_gui\libcntrl\literal_management_dialog.py`
- **LiteralManagementDialog** (L16) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_load_table`
    - `_get_selected_literal_name`
    - `_add_literal`
    - `_edit_literal`
    - `_delete_literal`
- **LiteralEditDialog** (L132) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_literal`

## `statable_gui\libcntrl\role_function_edit_dialog.py`
- **RoleFunctionEditDialog** (L17) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_load_data`
    - `_on_accept`
    - `get_role_function`

## `statable_gui\libcntrl\role_function_library.py`
- **RoleFunction** (L11) bases=[]
    - `__post_init__`
    - `qualified_name`
    - `to_dict`
    - `from_dict`
- **RoleFunctionLibrary** (L56) bases=[]
    - `__init__`
    - `_key`
    - `add`
    - `remove`
    - `get`
    - `list_all`
    - `to_dict`
    - `from_dict`

## `statable_gui\logger.py`
- **StaTableLogger** (L6) bases=[]
    - `__new__`
    - `_init_logger`
    - `set_log_callback`
    - `get_logger`
    - `debug`
    - `info`
    - `warning`
    - `error`
- **_TraceBallHandler** (L59) bases=['logging.Handler']
    - `__init__`
    - `set_callback`
    - `emit`

## `statable_gui\main_window.py`
- **MainWindow** (L75) bases=['QMainWindow']
    - `__init__`
    - `create_toolbar`
    - `create_menus`
    - `open_layer_settings`
    - `open_type_manager`
    - `open_global_defs_dialog`
    - `open_event_definition_dialog`
    - `open_event_delivery_settings`
    - `open_interrupt_settings`
    - `save_project`
    - `open_project`
    - `close_all_tabs`
    - `rename_current_tab`
    - `rename_tab_at`
    - `add_new_tab`
    - `add_state_machine_tab`
    - `close_tab`
    - `toggle_traceball`
    - `_get_current_state_machine`
    - `_get_current_data`
    - `_get_all_layers`
    - `open_validation_dialog`
    - `open_code_generation_dialog`
    - `open_code_generation_settings`
    - `save_generated_code_direct`

## `statable_gui\matrix_table.py`
- **MatrixTableWidget** (L101) bases=['QTableWidget']
    - `__init__`
    - `populate`
    - `_find_transitions`
    - `_generate_cell_label`
    - `_generate_title`
    - `open_transition_dialog`
    - `keyPressEvent`

## `statable_gui\preference_keys.py`
- (no classes)

## `statable_gui\preferences.py`
- **Preferences** (L8) bases=[]
    - `__init__`
    - `_apply_defaults`
    - `load`
    - `save`
    - `get`
    - `set`
    - `__getattr__`
    - `__setattr__`

## `statable_gui\role_function_dialog.py`
- **RoleFunctionDialog** (L9) bases=['QDialog']
    - `__init__`
    - `_on_accept`
    - `get_role_function`

## `statable_gui\sample_data.py`
- (no classes)

## `statable_gui\symbol_picker.py`
- **SymbolPickerWidget** (L13) bases=['QWidget']
    - `__init__`
    - `refresh_list`
    - `_matches`
    - `_on_item_double_clicked`
    - `register_variable`
    - `register_flag`
    - `open_global_definitions`

## `statable_gui\traceball.py`
- **TraceBallWidget** (L7) bases=['QDockWidget']
    - `__init__`
    - `append_log`
    - `clear`

## `statable_gui\transition_editor_direct\__init__.py`
- (no classes)

## `statable_gui\transition_editor_direct\actions_tab.py`
- **_ActionGroup** (L49) bases=['QGroupBox']
    - `__init__`
    - `set_role_functions`
    - `set_actions`
    - `get_actions`
    - `row_count`
    - `_append_row`
    - `_on_add`
    - `_on_delete`
    - `_on_move_up`
    - `_on_move_down`
    - `_swap`
- **ActionsTab** (L169) bases=['QWidget']
    - `__init__`
    - `set_role_functions`
    - `_build_ui`
    - `row_count`
    - `add_action`
    - `get_actions`
    - `set_actions`
    - `delete_action`
    - `move_up`
    - `_on_changed`

## `statable_gui\transition_editor_direct\code_widget.py`
- **CodeWidget** (L42) bases=['QPlainTextEdit']
    - `__init__`
    - `update_code`
    - `_get_layer_name`
    - `_context_type`
    - `_role_func_name`
    - `_call_stmt`
    - `_generate_code`
    - `_collect_child_labels_inline`
    - `_emit_relation_inline`
    - `_emit_transition_item`

## `statable_gui\transition_editor_direct\coverage_analyzer.py`
- **DuplicateTargetMap** (L19) bases=['dict']
    - `__eq__`
    - `__ne__`
- **CellReport** (L34) bases=[]
- **StateGraphReport** (L44) bases=[]
- **CoverageAnalyzer** (L50) bases=[]
    - `analyze_cell`
    - `analyze_state_graph`

## `statable_gui\transition_editor_direct\dialog.py`
- **ActionEditorDialog** (L56) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_load_draft`
    - `_save_draft`
    - `_sync_member_details`
    - `_on_content_changed`
    - `_on_refresh_preview`
    - `_on_accept`
    - `get_tab_names`

## `statable_gui\transition_editor_direct\draft.py`
- **SystemGlobal** (L36) bases=[]
    - `to_dict`
    - `from_dict`
- **TransitionParams** (L61) bases=[]
- **FlowItem** (L74) bases=[]
    - `display_text`
    - `to_dict`
    - `from_dict`
- **ActionDraft** (L108) bases=[]
    - `clear`
    - `get_role_func_name`
    - `to_dict`
    - `from_dict`

## `statable_gui\transition_editor_direct\edit_dialogs.py`
- **BaseEditDialog** (L11) bases=['QDialog']
    - `__init__`
    - `_add_buttons`
- **FunctionEditDialog** (L29) bases=['BaseEditDialog']
    - `__init__`
    - `get_result`
- **TransitionEditDialog** (L50) bases=['BaseEditDialog']
    - `__init__`
    - `_add_pre`
    - `_del_pre`
    - `_open_condition_builder`
    - `get_result`

## `statable_gui\transition_editor_direct\overview_tab.py`
- **OverviewTab** (L23) bases=['QWidget']
    - `__init__`
    - `_build_ui`
    - `refresh`
    - `get_summary_text`
    - `_refresh_cell_view`
    - `_refresh_graph_view`

## `statable_gui\transition_editor_direct\palette_widget.py`
- **PaletteListWidget** (L17) bases=['QListWidget']
    - `__init__`
    - `mimeData`
    - `startDrag`
    - `mouseDoubleClickEvent`
- **PaletteWidget** (L85) bases=['QWidget']
    - `__init__`
    - `_setup_ui`
    - `_generate_unique_name`
    - `_add_function`
    - `_add_transition`
    - `_on_function_item_edit_requested`
    - `_on_transition_item_edit_requested`
    - `refresh_lists`

## `statable_gui\transition_editor_direct\relations_edit_dialog.py`
- **RelationsEditDialog** (L33) bases=['QDialog']
    - `__init__`
    - `_load`
    - `_on_accept`
    - `get_members`
    - `get_relation`

## `statable_gui\transition_editor_direct\relations_tab.py`
- **RelationsTab** (L34) bases=['QWidget']
    - `__init__`
    - `_build_ui`
    - `set_member_details`
    - `_get_available_labels`
    - `row_count`
    - `add_relation`
    - `delete_relation`
    - `get_relations`
    - `set_relations`
    - `_on_double_click`
    - `_add`
    - `_edit`

## `statable_gui\transition_editor_direct\system_global_dialog.py`
- **SystemGlobalDialog** (L11) bases=['QDialog']
    - `__init__`
    - `_load`
    - `_add`
    - `_delete`

## `statable_gui\transition_editor_direct\transition_actions_dialog.py`
- **TransitionActionsDialog** (L16) bases=['QDialog']
    - `__init__`
    - `_add`
    - `_del`
    - `get_pre_actions`
    - `get_else_actions`

## `statable_gui\transition_editor_direct\transitions_tab.py`
- **TransitionsTab** (L44) bases=['QWidget']
    - `__init__`
    - `set_role_functions`
    - `set_states`
    - `_build_ui`
    - `_make_state_combo`
    - `_make_has_else_combo`
    - `_refresh_state_combo`
    - `_wire_else_link`
    - `_on_has_else_changed`
    - `row_count`
    - `_refresh_priority_column`
    - `_emit_changed`
    - `_on_cell_double_clicked`
    - `_edit_condition`
    - `_edit_actions`
    - `_edit_actions_current_row`
    - `_parse_csv`
    - `_csv`
    - `_set_cell_csv`
    - `add_transition`
    - `delete_transition`
    - `move_up`
    - `move_down`
    - `_swap_rows`
    - `_item_text`
    - `_widget_text`
    - `get_transitions`
    - `set_transitions`

## `statable_gui\validation_dialog.py`
- **ValidationDialog** (L31) bases=['QDialog']
    - `__init__`
    - `_setup_ui`
    - `_setup_validation_tab`
    - `_setup_prompt_tab`
    - `_setup_response_tab`
    - `_setup_changes_tab`
    - `_run_validation`
    - `_copy_prompt`
    - `_paste_response`
    - `_parse_response`
    - `_apply_changes`

## `statable_gui\widgets.py`
- **MermaidWidget** (L146) bases=['QWidget']
    - `__init__`
    - `set_mermaid_code`
    - `_on_load_finished`
    - `_request_svg_size`
    - `_apply_svg_size`
- **SettingsPanel** (L602) bases=['QWidget']
    - `__init__`
    - `_emit_settings_changed`
    - `populate`
    - `populate_role_table`
    - `on_state_table_cell_double_clicked`
    - `add_state`
    - `delete_state`
    - `open_event_definition`
    - `add_role_function`
    - `delete_role_function`
    - `on_state_table_item_changed`
    - `on_role_table_item_changed`
    - `apply_changes`
- **StateMachineTab** (L903) bases=['QWidget']
    - `__init__`
    - `update_mermaid`
