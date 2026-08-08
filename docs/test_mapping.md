# Acceptance criteria and test mapping

## Stage 00 — Project scaffold

| Requirement | Automated evidence |
|---|---|
| Runnable application shell | `tests/test_scaffold.py::test_application_shell_and_versioned_contract_are_available` |
| Stable version constants and schemas | `tests/test_scaffold.py::test_application_shell_and_versioned_contract_are_available` |
| Offline fixture/model interfaces | `tests/test_data_pipeline.py`, `tests/test_model_service.py` |
| Error-handling foundation | `tests/test_scaffold.py::test_unknown_route_uses_controlled_http_error`, `tests/test_api.py` |
| Deterministic preprocessing | `tests/test_data_pipeline.py`, `tests/test_features.py` |
| Invalid/empty threshold inputs rejected | `test_threshold_selection_rejects_invalid_validation_inputs` |
| Minimal feedback persistence | `tests/test_api.py::test_health_demo_assessment_and_override_flow` |
| Blocking model/SQLite handlers use worker threads | `test_blocking_model_batch_and_sqlite_routes_use_fastapi_threadpool` |

All future User Story tests must identify the User Story and AC in their test
docstring or in this mapping.

## Stage 01 — US1.1 Account intake

| Acceptance criterion | Automated evidence |
|---|---|
| AC1 valid input starts one intake and UI shows loading | `test_ac1_ac3_valid_identifier_starts_exactly_one_normalised_intake`, `test_ac1_ac2_ac6_page_has_loading_validation_and_accessible_labels` |
| AC2 blank/unsupported input blocked with adjacent message | `test_ac2_blank_unsupported_and_unknown_identifiers_are_controlled`, `test_ac1_ac2_ac6_page_has_loading_validation_and_accessible_labels` |
| AC3 optional @ normalisation | `test_ac1_ac3_valid_identifier_starts_exactly_one_normalised_intake` |
| AC4 representative Low/Medium/High demos | `test_ac4_ac5_demo_selector_has_representative_deterministic_scenarios`, `test_tutor_feedback_home_page_states_purpose_and_fixed_model_information_link` |
| AC5 deterministic and offline path | `test_ac4_ac5_demo_selector_has_representative_deterministic_scenarios` |
| AC6 labelled, keyboard-native controls | `test_ac1_ac2_ac6_page_has_loading_validation_and_accessible_labels` |

## Stage 02 — US1.2 Account preview

| Acceptance criterion | Automated evidence |
|---|---|
| AC1 grouped identifier/profile/activity/network evidence | `test_ac1_preview_groups_identifier_profile_activity_and_network` |
| AC2 missing values named and not imputed | `test_ac2_missing_values_are_null_and_named_without_imputation` |
| AC3 approved public fields only | `test_ac3_only_approved_public_fields_are_exposed` |
| AC4 source and model content separated | `test_ac4_source_data_is_explicitly_separate_from_model_output` |

## Stage 03 — US2.1 Feature completeness

| Acceptance criterion | Automated evidence |
|---|---|
| AC1 completeness calculated/displayed before score | `test_ac1_completeness_is_calculated_and_displayed_before_scoring` |
| AC2 below 50% is Insufficient data without band | `test_ac2_below_half_is_insufficient_without_risk_band` |
| AC3 exactly 50% eligible with caveat | `test_ac3_exactly_half_is_eligible_and_keeps_caveat` |
| AC4 missing features use plain labels | `test_ac4_missing_required_features_use_plain_language` |

## Stage 04 — US2.2 Risk scoring

| Acceptance criterion | Automated evidence |
|---|---|
| AC1 0–100 score | `test_ac1_ac2_ac3_real_model_returns_versioned_score_band_and_time` |
| AC2 exactly one versioned band/boundaries | `test_ac1_ac2_ac3_real_model_returns_versioned_score_band_and_time`, `test_ac2_ac4_representative_fixtures_are_deterministic_across_bands`, `test_tutor_feedback_dataset_selector_examples_match_documented_bands` |
| AC3 model version and time | `test_ac1_ac2_ac3_real_model_returns_versioned_score_band_and_time` |
| AC4 deterministic input/model result | `test_ac2_ac4_representative_fixtures_are_deterministic_across_bands` |
| AC5 text plus accessible colour classes | `test_ac5_ac6_ui_uses_text_plus_contrast_classes_and_no_definitive_label` |
| AC6 no definitive bot/human label | `test_ac5_ac6_ui_uses_text_plus_contrast_classes_and_no_definitive_label` |
| AC7 recoverable failure without partial score | `test_ac7_scoring_failure_is_recoverable_without_partial_score`, `test_finite_out_of_range_probabilities_use_malformed_model_contract` |

## Stage 05 — US3.1 Explanation and uncertainty

| AC | Automated evidence |
|---|---|
| AC1–AC3 top factors/order/direction/plain values | `test_ac1_ac2_ac3_top_three_are_ordered_plain_and_observed` |
| AC4–AC6 shared context/disclaimer/uncertainty | `test_ac4_ac5_ac6_factors_uncertainty_and_score_share_result_context` |
| AC7 prohibited certainty/enforcement wording | `test_ac7_ui_avoids_certainty_guilt_and_enforcement_claims` |

## Stage 06 — US4.1 Confirm or override

| AC | Automated evidence |
|---|---|
| AC1–AC2 completed assessment and override reason | `test_ac1_ac2_decision_requires_assessment_and_override_reason` |
| AC3–AC4 human final/no action/minimal fields | `test_ac3_ac4_minimal_feedback_and_no_platform_action` |
| AC5 acknowledgement/duplicate prevention | `test_ac5_acknowledgement_and_duplicate_prevention` |
| Server restart and bounded assessment context | `test_assessment_context_survives_application_restart`, `test_expired_assessment_contexts_are_purged_and_rejected` |

## Stage 07 — US1.3 Recovery and reset

| AC | Automated evidence |
|---|---|
| AC1–AC2 controlled/distinct errors and actions | `test_ac1_ac2_controlled_source_timeout_and_unknown_states`, `test_ac1_model_timeout_and_malformed_response_are_controlled` |
| AC3–AC6 retry, stale-state clearing, reset focus/continuity | `test_ac3_ac4_ac5_ac6_ui_retry_reset_clears_state_and_restores_focus` |
| Cross-origin Follow-up preflight | `test_follow_up_cors_preflight_allows_put` |

## Stage 08 — US4.2 Data protection

| AC | Automated evidence |
|---|---|
| AC1/AC3 no raw profile; minimal persistence only | `test_ac1_ac3_only_minimal_feedback_table_persists` |
| AC2 safe logs | `test_ac2_unexpected_logs_exclude_payload_token_and_identifier` |
| AC4 authorised-role access | `test_ac4_feedback_requires_authorised_role` |

## Stage 09 — US4.3 Follow-up

| AC | Automated evidence |
|---|---|
| AC1 completed/insufficient eligibility | `test_ac1_completed_and_insufficient_assessments_can_be_flagged` |
| AC2–AC3 reason, status, update/clear, role | `test_ac2_ac3_reason_update_clear_and_authorisation` |
| AC4–AC5 minimal record/no platform action | `test_ac4_ac5_minimal_record_and_no_platform_action` |
| Follow-up remains actionable after restart | `test_follow_up_context_survives_application_restart` |

## Stage 10 — US3.2 Model information

| AC | Automated evidence |
|---|---|
| AC1–AC2 verified scope, versions, datasets, metrics and dates | `test_ac1_ac2_page_reports_verified_scope_versions_and_evidence` |
| AC3 exclusions, shift/drift, false positives and enforcement prohibition | `test_ac3_page_discloses_required_risks_and_prohibition` |
| AC4 direct link from scored and Insufficient data results | `test_ac4_scored_and_insufficient_result_sections_link_directly` |
| Tutor usability: plain guidance before optional technical record | `test_tutor_feedback_explains_features_and_metrics_in_plain_language`, `test_tutor_feedback_leads_with_plain_language_and_folds_technical_record` |

## Stage 11 — US5.1 Batch assessment

| AC | Automated evidence |
|---|---|
| AC1 file type, exact header and row limit | `test_ac1_file_type_header_and_row_limit_are_validated` |
| AC1–AC2 duplicates, identifiers and partial success | `test_ac1_ac2_duplicates_and_invalid_rows_do_not_block_valid_rows` |
| AC2 Insufficient data and unavailable-row isolation | `test_ac2_insufficient_and_unknown_rows_are_reported_independently` |
| Account ID/username aliases deduplicate canonically | `test_account_id_and_username_alias_are_one_batch_account` |
| AC3–AC4 visible progress/counts and no platform action | `test_ac3_ac4_page_exposes_progress_counts_and_no_action_wording` |

## Stage 12 — US5.2 Sort and filter

| AC | Automated evidence |
|---|---|
| AC1 risk sorting and all three filters | `test_ac1_sort_and_all_required_filters` |
| AC2 active controls and matching count | `test_ac2_active_filters_and_matching_count_are_described` |
| AC3–AC4 clear restores source order without mutation | `test_ac3_ac4_clear_state_restores_order_without_mutating_source` |
| AC1–AC3 accessible browser controls | `test_ac1_ac2_ac3_browser_controls_are_present` |

## Stage 13 — Integration and regression

| Release check | Automated evidence |
|---|---|
| Main demo and human review path | `test_release_main_demo_path_and_human_review_contract` |
| Batch/single consistency | `test_release_batch_and_single_account_results_are_consistent` |
| Minimal pseudonymous persistence | `test_release_persistence_remains_minimal_and_pseudonymous` |
| Accessibility landmarks and labels | `test_release_shell_has_required_accessibility_landmarks_and_labels` |
| Controlled error matrix | `test_release_controlled_error_matrix_has_no_traceback` |
| No stale single/batch UI state | `test_release_reset_code_clears_single_and_batch_stale_state` |
| Model-information return restores the current assessment | `test_tutor_feedback_preserves_current_assessment_across_model_information` |
| Strict session schema, nullable factor fallback and review-state restoration | `test_versioned_snapshot_restores_review_state_and_rejects_corruption` |
| Browser timeout/non-JSON/follow-up/hidden-state safeguards | `test_api_client_handles_non_json_and_timeout_failures`, `test_follow_up_controller_exposes_busy_and_persistence_guards` |
