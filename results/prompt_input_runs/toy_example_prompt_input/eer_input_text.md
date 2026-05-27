# Textual EER Input

This file was generated from an expert-defined EER-YAML file.
It is used as controlled input for LLM conceptual-to-logical schema generation.

## Schema Metadata

- Schema ID: toy_example_v1
- Dataset name: toy_example
- Dataset complexity: low
- Version: 0.1
- Source description: Synthetic toy schema for testing the benchmark pipeline.
- Notes: This example is not a real dataset. It is used only for testing scripts and evaluation logic.

## Model Scope

Included entities:
- Customer
- CustomerProfile
- Order
- Product

Excluded entities:
- none

Inclusion criteria: Minimal schema with basic EER-to-relational mapping cases.
Exclusion criteria: No advanced specialization or weak entity cases included.

## Complexity Metadata

- Number of entities: 4
- Number of relationships: 3
- Number of attributes: 9
- Number of specializations: 0
- Number of weak entities: 0
- Number of multivalued attributes: 0
- Number of relationship attributes: 1
## Entities

### Entity: Customer

- ID: E001
- Type: regular
- Description: A customer who places orders.
- Aliases: Client

Identifier:
- Primary identifier name: CustomerPK
- Primary identifier attributes: customer_id
- Identifier type: surrogate
- Candidate identifiers: none
- Alternate keys:
  - CustomerEmailUK: email

Attributes:
- customer_id
  - Description: Unique customer identifier.
  - Data type: integer
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: true
  - Notes: none
- name
  - Description: Customer name.
  - Data type: string
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: false
  - Notes: none
- email
  - Description: Customer email.
  - Data type: string
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: false
  - Notes: Candidate unique attribute.

### Entity: CustomerProfile

- ID: E002
- Type: regular
- Description: Optional profile information for a customer.
- Aliases: Profile

Identifier:
- Primary identifier name: CustomerProfilePK
- Primary identifier attributes: customer_id
- Identifier type: derived_from_relationship
- Candidate identifiers: none
- Alternate keys: none

Attributes:
- bio
  - Description: Short customer biography.
  - Data type: text
  - Required: false
  - Nullable: true
  - Attribute kind: simple
  - Cardinality: min 0, max 1
  - Identifier attribute: false
  - Notes: none
- birth_date
  - Description: Customer birth date.
  - Data type: date
  - Required: false
  - Nullable: true
  - Attribute kind: simple
  - Cardinality: min 0, max 1
  - Identifier attribute: false
  - Notes: none

### Entity: Order

- ID: E003
- Type: regular
- Description: A purchase order placed by a customer.
- Aliases: Purchase

Identifier:
- Primary identifier name: OrderPK
- Primary identifier attributes: order_id
- Identifier type: surrogate
- Candidate identifiers: none
- Alternate keys: none

Attributes:
- order_id
  - Description: Unique order identifier.
  - Data type: integer
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: true
  - Notes: none
- order_date
  - Description: Date when the order was placed.
  - Data type: date
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: false
  - Notes: none

### Entity: Product

- ID: E004
- Type: regular
- Description: A product that can appear in orders.
- Aliases: Item

Identifier:
- Primary identifier name: ProductPK
- Primary identifier attributes: product_id
- Identifier type: surrogate
- Candidate identifiers: none
- Alternate keys: none

Attributes:
- product_id
  - Description: Unique product identifier.
  - Data type: integer
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: true
  - Notes: none
- product_name
  - Description: Product name.
  - Data type: string
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: false
  - Notes: none
- price
  - Description: Product unit price.
  - Data type: float
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Cardinality: min 1, max 1
  - Identifier attribute: false
  - Notes: none
## Relationships

### Relationship: CustomerPlacesOrder

- ID: R001
- Type: association
- Arity: 2
- Description: A customer places zero or more orders. Each order belongs to exactly one customer.
- Aliases: places

Participants:
- Entity: Customer
  - Role: customer
  - Cardinality: min 0, max many
  - Participation: optional
  - Identifying: false
  - Notes: none
- Entity: Order
  - Role: order
  - Cardinality: min 1, max 1
  - Participation: mandatory
  - Identifying: false
  - Notes: none

Relationship attributes:
- none

Relationship constraints:
- Cardinality class: one_to_many
- Is functional: true
- Functional from: Order
- Functional to: Customer
- Requires relationship table: false
- Notes: Map as customer_id FK in Order.

### Relationship: OrderContainsProduct

- ID: R002
- Type: association
- Arity: 2
- Description: An order may contain many products, and a product may appear in many orders.
- Aliases: contains

Participants:
- Entity: Order
  - Role: order
  - Cardinality: min 1, max many
  - Participation: mandatory
  - Identifying: false
  - Notes: none
- Entity: Product
  - Role: product
  - Cardinality: min 0, max many
  - Participation: optional
  - Identifying: false
  - Notes: none

Relationship attributes:
- quantity
  - Data type: integer
  - Required: true
  - Nullable: false
  - Attribute kind: simple
  - Notes: none

Relationship constraints:
- Cardinality class: many_to_many
- Is functional: false
- Functional from: not_specified
- Functional to: not_specified
- Requires relationship table: true
- Notes: Map as relationship table OrderProduct.

### Relationship: CustomerHasProfile

- ID: R003
- Type: association
- Arity: 2
- Description: A customer may have at most one profile, and each profile belongs to exactly one customer.
- Aliases: has_profile

Participants:
- Entity: Customer
  - Role: customer
  - Cardinality: min 0, max 1
  - Participation: optional
  - Identifying: false
  - Notes: none
- Entity: CustomerProfile
  - Role: profile
  - Cardinality: min 1, max 1
  - Participation: mandatory
  - Identifying: false
  - Notes: none

Relationship attributes:
- none

Relationship constraints:
- Cardinality class: one_to_one
- Is functional: true
- Functional from: CustomerProfile
- Functional to: Customer
- Requires relationship table: false
- Notes: Preferred mapping keeps CustomerProfile as a separate table with customer_id as PK and FK.
## Specialization and Generalization

No specialization/generalization structures specified.
## Global Constraints

### Key constraints
- ID: KC001
  - Details: {"applies_to": "Customer", "attributes": ["customer_id"], "constraint_type": "primary"}
  - Notes: none
- ID: KC002
  - Details: {"applies_to": "Order", "attributes": ["order_id"], "constraint_type": "primary"}
  - Notes: none
- ID: KC003
  - Details: {"applies_to": "Product", "attributes": ["product_id"], "constraint_type": "primary"}
  - Notes: none

### Participation constraints
- ID: PC001
  - Details: {"entity": "Order", "relationship": "CustomerPlacesOrder", "min": 1, "max": 1, "mandatory": true}
  - Notes: Each order must reference exactly one customer.

### Cardinality constraints
- ID: CC001
  - Description: Many-to-many relationship requiring relationship table.
  - Details: {"relationship": "OrderContainsProduct"}
  - Notes: none

### Inclusion constraints
- none

### Exclusion constraints
- none

### Business rules
- none
## Expert Notes

### Assumptions
- CustomerProfile is optional for Customer but mandatory for CustomerProfile.

### Ambiguities
- CustomerHasProfile may be mapped as a separate profile table or merged into Customer.

### Mapping-relevant observations
- OrderContainsProduct must be mapped as a relationship table because it is many-to-many and has quantity.

### Excluded details
- none
## Task

Generate a logical relational schema in the benchmark JSON format.

Important requirements:
- Use only the information supported by this EER input.
- Do not invent unsupported entities, attributes, keys, relationships, or constraints.
- Preserve identifiers, cardinalities, participation constraints, relationship attributes, and specialization/generalization semantics.
- If more than one mapping is possible, choose the most justified mapping and document the decision in the output notes.
- Return only the relational JSON when answering the prompt.
