# Data Classification

Classify important project data during Discovery.

## Public

Approved for public disclosure.

Examples: public marketing content, published documentation.

## Internal

Non-public operational information with limited impact if disclosed.

Examples: ordinary internal configuration without credentials, internal process notes.

## Confidential

Business/customer information whose disclosure could cause harm or contractual/privacy impact.

Examples: customer records, non-public contracts, business analytics, employee data.

## Restricted

Highest protection tier. Unauthorized disclosure or modification can cause material security, legal, financial, safety or privacy harm.

Examples include credentials/tokens/private keys, government identifiers, health data, payment/financial data, authentication factors, sensitive audit/security records.

## Required design decisions

For Confidential/Restricted data define:

- who may access it;
- tenant/object authorization rules;
- storage location;
- retention/deletion;
- logging/redaction;
- encryption expectations;
- export/download rules;
- backup handling;
- incident implications.
