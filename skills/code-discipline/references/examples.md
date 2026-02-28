# Code Discipline — Examples

Concrete before/after examples for each principle. Examples use JavaScript for
consistency, but the patterns apply to any language.

---

## Change Only What's Asked

User asked to rename `getUser` to `fetchUser`.

**Bad** — also reformatted imports and added types to unrelated functions:
```
import {
  fetchUser,          // renamed (requested)
  getOrders,
  getProducts,
} from './api';       // reformatted (not requested)

function fetchUser(id) { ... }           // renamed (requested)

function getOrders(userId): Order[] {    // added return type (not requested)
  ...
}
```

**Good** — only the rename:
```
import { fetchUser, getOrders, getProducts } from './api';

function fetchUser(id) { ... }
```

---

## No Speculative Code

User asked for a function to format a date as "Jan 1, 2025".

**Bad** — added configurable format, locale support, error handling:
```
function formatDate(date, options = {}) {
  const {
    format = 'medium',
    locale = 'en-US',
    fallback = 'Invalid date',
  } = options;

  try {
    if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
      return fallback;
    }
    return new Intl.DateTimeFormat(locale, { dateStyle: format }).format(date);
  } catch (e) {
    console.error('Date formatting failed:', e);
    return fallback;
  }
}
```

**Good** — does exactly what was asked:
```
function formatDate(date) {
  return date.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
}
```

---

## Match Existing Patterns

Existing codebase uses snake_case and explicit loops.

**Bad** — introduced camelCase and functional style into a snake_case codebase:
```
def calculateTotalPrice(cartItems):
    return sum(item.price * item.qty for item in cartItems if item.is_active)
```

**Good** — matched the project's existing conventions:
```
def calculate_total_price(cart_items):
    total = 0
    for item in cart_items:
        if item.is_active:
            total += item.price * item.qty
    return total
```

---

## Delete Completely

User asked to remove the deprecated `legacyAuth` function.

**Bad** — commented out, added markers, kept re-export:
```
// REMOVED: legacy authentication - use newAuth instead
// function legacyAuth(token) {
//   return validateLegacyToken(token);
// }

// Kept for backwards compatibility
export const legacyAuth = (...args) => {
  console.warn('legacyAuth is deprecated, use newAuth');
  return newAuth(...args);
};
```

**Good** — deleted the function and its import/export references:
```
(function and all references removed entirely)
```

---

## Comments Explain Why

**Bad** — restating the code:
```
// Check if user is admin
if (user.role === 'admin') {
  // Grant full access
  permissions = FULL_ACCESS;
}

// Initialize the counter to zero
let count = 0;
```

**Good** — explaining non-obvious reasoning:
```
// Admin bypass: skip rate limiting since internal dashboards
// generate bursts that would trigger false positives
if (user.role === 'admin') {
  permissions = FULL_ACCESS;
}
```

---

## Clarity Over Cleverness

**Bad** — compact but hard to follow:
```
const result = data?.items?.filter(x => x.active && !x.deleted)
  .reduce((a, b) => ({...a, [b.type]: [...(a[b.type] || []), b]}), {});

const label = count === 0 ? 'none' : count === 1 ? 'single' : count < 5 ? 'few' : 'many';
```

**Good** — clear and scannable:
```
const activeItems = data?.items?.filter(item => item.active && !item.deleted) ?? [];

const itemsByType = {};
for (const item of activeItems) {
  if (!itemsByType[item.type]) {
    itemsByType[item.type] = [];
  }
  itemsByType[item.type].push(item);
}

function countLabel(count) {
  if (count === 0) return 'none';
  if (count === 1) return 'single';
  if (count < 5) return 'few';
  return 'many';
}
```

---

## Validate at Boundaries

**Bad** — defensive checks on internal, typed data:
```
function calculateTotal(cart) {
  if (!cart) throw new Error('Cart is required');
  if (!Array.isArray(cart.items)) throw new Error('Cart items must be array');

  return cart.items.reduce((sum, item) => {
    if (!item) return sum;
    if (typeof item.price !== 'number') return sum;
    if (typeof item.quantity !== 'number') return sum;
    return sum + (item.price * item.quantity);
  }, 0);
}
```

**Good** — validate where untrusted data enters, trust internal code:
```
// Validation at the system boundary (route handler, CLI parser, etc.)
function handleCheckout(requestBody) {
  const cart = parseAndValidateCart(requestBody);  // rejects bad input here
  const total = calculateTotal(cart);
  return { total };
}

// Internal function trusts its callers
function calculateTotal(cart) {
  return cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
```
