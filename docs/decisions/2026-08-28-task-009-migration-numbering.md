# Task 009 migration numbering clarification

**Status:** REVIEWED — Central Brain correction

Task 009 / M8 uses Alembic revision `0009`.

The accepted M7 schema on canonical `main` ends at `0008`; therefore `0009` is the next unused schema revision. The `0010` label in the Task 009 persistence heading is a numbering typo and does not supersede the binding instruction to use the next unused revision after M7.

All M8 Stage A migration, backup, restore and regression acceptance evidence must target `0009`.
