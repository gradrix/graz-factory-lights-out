# Cohort C-v2 fixture gate — PASS

Manifest: `560c3e5645ed2d9ea91404e05aa4ddb2f4c9b1eb01f8629a98ec6e6ae738938b`. All 97 bound hashes verified. Original C manifest and all 95 original bound files remain unchanged. Twelve task contracts, source commit map, and budgets are unchanged.

| Recheck | Result |
|---|---|
| Known bad Luhn integer 0/1 output | Rejected by real Docker acceptance; conforming boolean reference passes |
| Allocation/calendar/matching references | All pass |
| Float quotas, persistent calendar clamp, greedy matching mutants | All rejected |
| Missing tests, failing tests, missing documentation | All rejected |
| Shared comparator | Identical recursive type-and-value comparator in all 12 task oracles; nested bool/int swaps rejected; identical nested values accepted |
| API/CLI/immutability coverage | All use new comparator; baseline identity now includes True and False |

No remaining blocker identified for exposing this frozen cohort. The previous JSON boolean false acceptance is closed. This proportional fixture gate does not establish complete test meaningfulness, model capability, or exhaustive oracle correctness; existing semantic review requirements remain relevant.

Reproduction: `python3 .scratch/.sflo/03-autonomy-review/qa-cohort-c-v2-probe.py` (exit 0). Complete executable probe and detailed real Docker outputs: `qa-cohort-c-v2-probe.py`, `qa-cohort-c-v2-probe.json`, `qa-cohort-c-v2-probe.log`. Four conforming controls and seven rejecting mutations ran. No GPU/model calls or fixture/product mutations.
