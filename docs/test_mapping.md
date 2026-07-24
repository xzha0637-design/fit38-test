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
