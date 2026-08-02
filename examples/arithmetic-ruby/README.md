# arithmetic-ruby (evaluation sample)

Minimal **Ruby + RSpec** sample for arithmetic (+ mod). Keeps OCL as SoT while swapping the contract-test generation target from Vitest to RSpec.

No HTTP / GraphQL boundary (see [../arithmetic-api](../arithmetic-api) / [../arithmetic-graphql](../arithmetic-graphql)).

Does **not** use a language-native contracts gem (optional adoption deferred / opt-in).

## Contract locations

| Kind | Path |
|------|------|
| OCL | `contracts/Calculator.ocl` |
| Contract specs | `spec/contracts/calculator_spec.rb` |
| Implementation | `lib/calculator.rb` |

## Setup

```bash
bundle install
bundle exec rspec
```

## Using with solid_sdd

1. `solidsdd-apply-dbc` → OCL
2. `solidsdd-derive-tests` (target: RSpec / `adapters/ruby-rspec`)
3. `solidsdd-implement` → `lib/`
4. `solidsdd-verify` → `bundle exec rspec`
