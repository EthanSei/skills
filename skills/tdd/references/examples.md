# TDD — Examples

Concrete examples of test-driven development cycles. Examples show the pattern,
not a specific language — adapt to whatever framework the project uses.

---

## Example 1: Building a Function Step by Step

Task: Write a function that checks if a string is a valid email address
(contains exactly one `@` with non-empty parts on both sides).

### Cycle 1: Simplest valid case

**Red** — write the test:
```
test "valid email returns true"
  assert isValidEmail("user@example.com") == true
```
Run tests. Fails: `isValidEmail` does not exist.

**Green** — minimum implementation:
```
function isValidEmail(email)
  return email.contains("@")
```
Run tests. Passes.

**Refactor** — nothing to clean up yet.

### Cycle 2: Rejects missing @

**Red:**
```
test "string without @ returns false"
  assert isValidEmail("userexample.com") == false
```
Run tests. Passes already (our implementation handles this). Skip to next.

### Cycle 3: Rejects empty part before @

**Red:**
```
test "empty local part returns false"
  assert isValidEmail("@example.com") == false
```
Run tests. Fails: returns `true`.

**Green:**
```
function isValidEmail(email)
  parts = email.split("@")
  return parts.length == 2 and parts[0].length > 0 and parts[1].length > 0
```
Run tests. All pass.

### Cycle 4: Rejects multiple @

**Red:**
```
test "multiple @ returns false"
  assert isValidEmail("user@@example.com") == false
```
Run tests. Fails: split gives 3 parts, length check handles it. Actually passes.
Our `parts.length == 2` already covers this. Skip.

### Closing audit

Run full test suite. All pass. Lint clean. Done.

**Key takeaway**: each cycle adds one behavior. The implementation evolves
incrementally. We didn't design the final solution upfront.

---

## Example 2: Bug Fix with Regression Test

Task: Fix a bug where `calculateDiscount(100, 0)` returns `NaN` instead of `100`.

### Cycle 1: Reproduce the bug

**Red:**
```
test "zero discount returns original price"
  assert calculateDiscount(100, 0) == 100
```
Run tests. Fails: returns `NaN`. Good — we've reproduced the bug.

**Green** — find and fix the cause:
```
// Before (bug: division by zero in percentage calc)
function calculateDiscount(price, discountPercent)
  return price - (price / discountPercent)

// After
function calculateDiscount(price, discountPercent)
  return price * (1 - discountPercent / 100)
```
Run tests. Passes. All existing tests still pass.

**Closing audit**: full suite green, lint clean. The regression test stays
permanently.

---

## Example 3: Test Naming as Specification

Test names should read as a feature specification when listed together.

**Bad** — named after implementation:
```
test "test constructor"
test "test add method"
test "test remove method"
test "test edge case"
```

**Good** — named after behavior:
```
test "new cart has zero items"
test "adding a product increases item count by one"
test "adding the same product twice increases its quantity"
test "removing a product decreases item count by one"
test "removing the last unit of a product removes it from the cart"
test "total reflects sum of item prices times quantities"
```

---

## Example 4: Arrange-Act-Assert Pattern

Each test should have three clear phases.

**Bad** — mixed up, hard to follow:
```
test "user signup"
  db.clear()
  result = signup("alice", "alice@test.com")
  assert result.success
  user = db.findByEmail("alice@test.com")
  assert user != null
  result2 = signup("alice", "alice@test.com")
  assert result2.success == false
  assert result2.error == "email taken"
```

**Good** — one behavior per test, clear structure:
```
test "successful signup returns the new user"
  // Arrange
  db = emptyDatabase()

  // Act
  result = signup(db, "alice", "alice@test.com")

  // Assert
  assert result.success == true
  assert result.user.name == "alice"

test "signup with existing email fails"
  // Arrange
  db = emptyDatabase()
  signup(db, "alice", "alice@test.com")

  // Act
  result = signup(db, "bob", "alice@test.com")

  // Assert
  assert result.success == false
  assert result.error == "email taken"
```

---

## Example 5: Characterization Tests Before Refactoring

Task: Refactor `processOrder` to extract tax calculation, then add a new
tax-exempt order type.

### Step 1: Characterize existing behavior

Before changing anything, lock down what currently works:
```
test "standard order includes 10% tax"
  order = createOrder(type: "standard", subtotal: 100)
  result = processOrder(order)
  assert result.tax == 10
  assert result.total == 110

test "premium order includes 10% tax"
  order = createOrder(type: "premium", subtotal: 200)
  result = processOrder(order)
  assert result.tax == 20
  assert result.total == 220
```
Run tests. Pass. Existing behavior is now documented and protected.

### Step 2: Refactor under green tests

Extract tax calculation:
```
function calculateTax(subtotal)
  return subtotal * 0.10

function processOrder(order)
  tax = calculateTax(order.subtotal)
  return { tax: tax, total: order.subtotal + tax }
```
Run tests. Still pass. Refactoring successful.

### Step 3: TDD the new feature

Now proceed with normal red-green-refactor for tax-exempt orders:
```
test "tax-exempt order has zero tax"
  order = createOrder(type: "tax-exempt", subtotal: 100)
  result = processOrder(order)
  assert result.tax == 0
  assert result.total == 100
```
Red. Implement. Green. Closing audit. Done.
