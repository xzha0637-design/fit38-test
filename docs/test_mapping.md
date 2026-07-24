# Acceptance criteria and test mapping

## Stage 00 — Project scaffold

| Requirement | Automated evidence |
|---|---|
| Runnable application shell | `tests/test_scaffold.py::test_application_shell_and_versioned_contract_are_available` |
| Stable version constants and schemas | `tests/test_scaffold.py::test_application_shell_and_versioned_contract_are_available` |
| Offline fixture/model interfaces | `tests/test_data_pipeline.py`, `tests/test_model_service.py` |
| Error-handling foundation | `tests/test_scaffold.py::test_unknown_route_uses_controlled_http_error`, `tests/test_api.py` |
| Deterministic preprocessing | `tests/test_data_pipeline.py`, `tests/test_features.py` |
| Minimal feedback persistence | `tests/test_api.py::test_health_demo_assessment_and_override_flow` |

All future User Story tests must identify the User Story and AC in their test
docstring or in this mapping.

## Stage 01 — US1.1 Account intake

| Acceptance criterion | Automated evidence |
|---|---|
| AC1 valid input starts one intake and UI shows loading | `test_ac1_ac3_valid_identifier_starts_exactly_one_normalised_intake`, `test_ac1_ac2_ac6_page_has_loading_validation_and_accessible_labels` |
| AC2 blank/unsupported input blocked with adjacent message | `test_ac2_blank_unsupported_and_unknown_identifiers_are_controlled`, `test_ac1_ac2_ac6_page_has_loading_validation_and_accessible_labels` |
| AC3 optional @ normalisation | `test_ac1_ac3_valid_identifier_starts_exactly_one_normalised_intake` |
| AC4 representative Low/Medium/High demos | `test_ac4_ac5_demo_selector_has_representative_deterministic_scenarios` |
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
