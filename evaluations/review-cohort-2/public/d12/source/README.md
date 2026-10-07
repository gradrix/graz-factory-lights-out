# Release artifact selector

Existing action artifact_ids is exposed through api.dispatch and python cli.py, accepting one JSON object on stdin and writing one JSON result.

Add action select with artifacts:list of {id:unique nonempty string,platform:string,version:string,yanked:boolean}, platform:string, major:integer 0..1000. At most 200 artifacts. Every version is exactly three unsigned ASCII decimal components with no leading zero except 0, each 0..1000, separated by periods; versions have no prerelease/build suffix. Return null when no eligible artifact exists. Eligible means matching exact platform, major component equal to requested major, and yanked=false. Otherwise return {id,version} for numerically greatest (major,minor,patch), breaking equal-version ties by smallest id in Python string order. Input order never breaks ties. Preserve version spelling and input objects.

Example (SQLite requires the documented database to already exist):

```sh
printf '%s\n' '{"action": "select", "artifacts": [{"id": "a", "platform": "linux", "version": "1.9.9", "yanked": false}, {"id": "b", "platform": "linux", "version": "1.10.0", "yanked": false}, {"id": "c", "platform": "linux", "version": "2.0.0", "yanked": false}], "platform": "linux", "major": 1}' | python cli.py
```

Run tests with python -m unittest discover. Inputs remain unchanged and failures follow the documented CLI error contract.
