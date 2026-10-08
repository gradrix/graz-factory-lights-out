# Existing JSON utility

Use `python cli.py` with one JSON object on stdin. Existing action: weight. Domain functions accept the payload object; api.dispatch routes it. CLI reports ValueError/KeyError with stderr and exit 2.

## New usage

Action cache with capacity (nonnegative integer total weight) and operations (list). Start empty. Operation put has op='put',key:string,value:JSON,weight:positive integer; get has op='get',key:string. Invalid capacity/weight raises ValueError. Return {results:list,entries:list}: entries in least-to-most recently used order, each {key,value,weight}. A get hit returns {hit:true,value:stored value} and promotes key to most recent; miss returns {hit:false,value:null} without changing order. A successful put returns {stored:true,evicted:[keys in eviction order]}; replace existing key, mark it most recent, then evict oldest OTHER entries until total weight<=capacity. Replacement of the same key is not an eviction. If new weight>capacity, return {stored:false,evicted:[]} and leave existing cache/order untouched, even if replacing an existing key. Put validates positive weight before testing fit. Empty operations returns empty arrays. Preserve action weight. Use a weighted capacity, not entry count.

Example:

```sh
printf '%s\n' '{"action": "cache", "capacity": 4, "operations": [{"op": "put", "key": "a", "value": 1, "weight": 2}, {"op": "put", "key": "b", "value": 2, "weight": 2}, {"op": "get", "key": "a"}, {"op": "put", "key": "c", "value": 3, "weight": 1}]}' | python cli.py
```

Output:

```json
{"results": [{"stored": true, "evicted": []}, {"stored": true, "evicted": []}, {"hit": true, "value": 1}, {"stored": true, "evicted": ["b"]}], "entries": [{"key": "a", "value": 1, "weight": 2}, {"key": "c", "value": 3, "weight": 1}]}
```

Inputs that violate the rules above raise ValueError; the CLI then prints the message on stderr and exits with status 2. Run the regression tests with `python -m unittest discover`.
