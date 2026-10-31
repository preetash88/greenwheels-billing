Feature: Payment Idempotency
  As the Greenwheels billing system
  I want to ensure that submitting the same payment reference twice
  does not create a duplicate credit on a driver account

  Business Rule: Payment facts are idempotent. Submitting the same
  payment_reference twice must not create duplicate credit.
  This is the highest priority rule (P0) because duplicate credits
  directly cause financial loss and cannot be easily reversed in an
  event-sourced system.

  Background:
    Given the stub service is running
    And driver "DRIVER-001" has an active lease

  Scenario: First payment is recorded successfully
    Given a billing cycle exists for driver "DRIVER-001" for week 10
    When a payment of 3500 KES is submitted with reference "PAY-IDEM-FIRST"
    Then the response status code should be 201
    And the payment status should be "recorded"
    And the payment reference in the response should be "PAY-IDEM-FIRST"

  Scenario: Duplicate payment reference is accepted but not double-credited
    Given a billing cycle exists for driver "DRIVER-001" for week 11
    And a payment of 3500 KES has already been made with reference "PAY-IDEM-DUP"
    When the same payment is submitted again with reference "PAY-IDEM-DUP"
    Then the response status code should be 200
    And the payment status should be "duplicate"
    And the message should confirm no duplicate credit was applied

  Scenario: Summary total paid does not increase after duplicate payment
    Given a billing cycle exists for driver "DRIVER-001" for week 12
    And a payment of 3500 KES has already been made with reference "PAY-IDEM-SUM"
    When the same payment is submitted again with reference "PAY-IDEM-SUM"
    Then the billing summary total paid should not have increased

  Scenario Outline: Idempotency holds across different payment references
    Given a billing cycle exists for driver "DRIVER-001" for week <week>
    And a payment of <amount> KES has already been made with reference "<reference>"
    When the same payment is submitted again with reference "<reference>"
    Then the response status code should be 200
    And the payment status should be "duplicate"

    Examples:
      | week | amount | reference       |
      | 20   | 3500   | PAY-OUTLINE-001 |
      | 21   | 3500   | PAY-OUTLINE-002 |
      | 22   | 3500   | PAY-OUTLINE-003 |