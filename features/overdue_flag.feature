Feature: Overdue Flag After Consecutive Missed Payments
  As the Greenwheels billing system
  I want to automatically flag a driver as overdue
  when they have 3 or more consecutive missed payments

  Business Rule: A driver with 3 consecutive missed payments must
  automatically be flagged as overdue in the summary.

  A missed payment is defined as a billing cycle whose due date
  has passed with no payment recorded against it.

  Background:
    Given the stub service is running
    And driver "DRIVER-004" has an active lease with no billing history

  Scenario: Driver with no missed payments is not overdue
    Given driver "DRIVER-004" has no billing cycles
    When the billing summary is requested for driver "DRIVER-004"
    Then the response status code should be 200
    And the account status should be "ok"
    And the missed payment count should be 0

  Scenario: Driver with 2 consecutive missed payments is not yet overdue
    Given driver "DRIVER-004" has 2 unpaid overdue billing cycles
    When the billing summary is requested for driver "DRIVER-004"
    Then the response status code should be 200
    And the account status should be "ok"
    And the missed payment count should be 2

  Scenario: Driver with exactly 3 consecutive missed payments is flagged overdue
    Given driver "DRIVER-004" has 3 unpaid overdue billing cycles
    When the billing summary is requested for driver "DRIVER-004"
    Then the response status code should be 200
    And the account status should be "overdue"
    And the missed payment count should be 3

  Scenario: Driver remains overdue with 4 consecutive missed payments
    Given driver "DRIVER-004" has 4 unpaid overdue billing cycles
    When the billing summary is requested for driver "DRIVER-004"
    Then the response status code should be 200
    And the account status should be "overdue"
    And the missed payment count should be 4

  Scenario Outline: Overdue threshold boundary conditions
    Given driver "DRIVER-004" has <missed_count> unpaid overdue billing cycles
    When the billing summary is requested for driver "DRIVER-004"
    Then the account status should be "<expected_status>"
    And the missed payment count should be <missed_count>

    Examples:
      | missed_count | expected_status |
      | 1            | ok              |
      | 2            | ok              |
      | 3            | overdue         |
      | 4            | overdue         |
      | 5            | overdue         |