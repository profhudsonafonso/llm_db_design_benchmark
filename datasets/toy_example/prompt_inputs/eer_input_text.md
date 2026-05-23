# Toy Example — Textual EER Input

Dataset: toy_example  
Complexity: low

## Entities

### Customer
Description: A customer who places orders.

Attributes:
- customer_id: integer, required, primary identifier
- name: string, required
- email: string, required, candidate unique attribute

### CustomerProfile
Description: Optional profile information for a customer.

Attributes:
- bio: text, optional
- birth_date: date, optional

Identifier:
- customer_id, derived from the one-to-one relationship with Customer

### Order
Description: A purchase order placed by a customer.

Attributes:
- order_id: integer, required, primary identifier
- order_date: date, required

### Product
Description: A product that can appear in orders.

Attributes:
- product_id: integer, required, primary identifier
- product_name: string, required
- price: float, required

## Relationships

### CustomerPlacesOrder
Type: binary one-to-many relationship

Participants:
- Customer role customer: min 0, max many, optional participation
- Order role order: min 1, max 1, mandatory participation

Semantics:
A customer can place zero or more orders. Each order must belong to exactly one customer.

Expected mapping:
This relationship is normally mapped as a customer_id foreign key in Order.

### OrderContainsProduct
Type: binary many-to-many relationship

Participants:
- Order role order: min 1, max many, mandatory participation
- Product role product: min 0, max many, optional participation

Relationship attribute:
- quantity: integer, required

Semantics:
An order may contain many products, and a product may appear in many orders.

Expected mapping:
This relationship must be mapped as a relationship table because it is many-to-many and has the relationship attribute quantity.

### CustomerHasProfile
Type: binary one-to-one relationship

Participants:
- Customer role customer: min 0, max 1, optional participation
- CustomerProfile role profile: min 1, max 1, mandatory participation

Semantics:
A customer may have at most one profile, and each profile belongs to exactly one customer.

Preferred mapping:
Create a separate CustomerProfile table with customer_id as both primary key and foreign key to Customer.

Acceptable alternative:
Merge CustomerProfile attributes bio and birth_date into Customer.

Not allowed:
Do not create an unrelated profile table without a foreign key to Customer.
Do not create a many-to-many relationship table for this relationship.

## Output Task

Generate a logical relational schema in the benchmark JSON format.
