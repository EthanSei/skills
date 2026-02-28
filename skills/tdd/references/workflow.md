# TDD Workflow — Detailed

Step-by-step decision guide for working through a task using test-driven
development.

## Phase 1: Understand Before You Test

Before writing the first test:

1. **Read the request** — understand what behavior is needed
2. **Find the test runner** — locate config files, check scripts, look at existing tests
3. **Identify behaviors** — break the request into a list of discrete, testable behaviors
4. **Order by dependency** — start with the simplest behavior that has no prerequisites

Write down your behavior list. Each item becomes one red-green-refactor cycle.

## Phase 2: Red-Green-Refactor Cycles

For each behavior in your list:

### Red: Write the Failing Test

```
1. Create or open the appropriate test file
2. Write ONE test for the next behavior
3. Run the test suite
4. Confirm the new test FAILS
5. Confirm it fails for the RIGHT reason:
   - Missing function/class → correct, write the implementation
   - Wrong return value → correct, fix the logic
   - Import error → fix the import first, re-run to get the real failure
   - Syntax error in test → fix the test, this is not a valid "red"
```

If the test passes immediately, either:
- The behavior already exists (skip this cycle)
- The test is wrong (it's not testing what you think)

### Green: Make It Pass

```
1. Write the simplest code that makes the test pass
2. Run the test suite
3. If tests pass → move to Refactor
4. If tests fail → read the error, fix your implementation, re-run
```

"Simplest code" means literally the minimum. Hard-code a return value if that
makes the test pass and you only have one test case. The next test will force
you to generalize.

### Refactor: Clean Up

```
1. Look for duplication between test cases or implementation
2. Look for unclear names or overly complex logic
3. Make ONE improvement at a time
4. Run tests after EACH change
5. If any test breaks → undo the change, try something smaller
6. When the code is clean and all tests pass → done with this cycle
```

Refactoring is optional if the code is already clean after the green step.
Do not refactor just to refactor.

## Phase 3: Closing Audit

After all cycles are complete:

```
1. Run the FULL test suite (not just your new tests)
   → All pass? Continue.
   → Failures? Fix them. Do not skip.

2. Run the linter/formatter (if the project has one)
   → Clean? Continue.
   → Errors? Fix them.

3. Run the type checker (if applicable)
   → Clean? Continue.
   → Errors? Fix them.

4. Run the build (if applicable)
   → Succeeds? Continue.
   → Fails? Fix it.

5. Review your tests:
   → Does each test name describe a behavior?
   → Does each test verify exactly one thing?
   → Are tests independent (no shared mutable state)?
   → Do test names read as a specification when listed?
```

## Decision Points

### "I don't know how to run tests in this project"

Ask the user. Do not guess, do not skip, do not write tests you can't run.

### "The existing tests are already failing"

Tell the user. Do not fix unrelated failures without asking. Note which tests
were already failing before your changes so you can distinguish your breakage
from pre-existing issues.

### "I need to refactor existing code to make my feature testable"

That refactoring is part of the work. Test the existing behavior first:
1. Write characterization tests for the current behavior
2. Refactor under those green tests
3. Then proceed with your new feature's TDD cycles

### "The user asked me not to write tests"

Respect the request. But note that you're skipping tests. If you see an
opportunity to add a quick, high-value test, mention it.

### "I'm fixing a bug"

Bug fixes are the best TDD candidate:
1. Write a test that reproduces the bug (should fail)
2. Fix the bug (test should pass)
3. You now have a regression test

### "I'm adding to existing code with no tests"

Start by understanding the existing behavior. Write a few characterization
tests for the code you're about to modify, then proceed with TDD for the new
behavior. Don't try to backfill full test coverage — just cover what you touch.

## Anti-Patterns

Avoid these common mistakes:

- **Writing all tests first** — write one, make it pass, then write the next
- **Testing implementation details** — test behavior, not internal structure
- **Skipping the red step** — if you didn't see the test fail, you don't know it works
- **Writing implementation before the test** — the whole point is test-first
- **Not running tests after refactoring** — refactoring can break things
- **Declaring done without the closing audit** — the audit is mandatory, not a suggestion
