#!/bin/bash
# Verify review-cohort-3: manifest integrity, acceptance, shipped tests, README examples, seeded-defect demos.
# Writes private/verification.txt. Python runs only inside Docker.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
COHORT=$(dirname "$HERE")
EVAL=$(dirname "$COHORT")
IMG=sha256:fb1118f126b507965df3c46fdfc52312dfd5262e7b6652ef510bd9298f69a6bc
OUT="$HERE/verification.txt"
RUN=(docker run --rm --pull never --network none --read-only --tmpfs /tmp:rw,size=128m --user 1000:1000)
fail=0
{
echo "review-cohort-3 verification"
echo "image $IMG ($("${RUN[@]}" $IMG python -V 2>&1))"
echo "manifest sha256 $(sha256sum "$COHORT/manifest.json" | cut -d' ' -f1)"
"${RUN[@]}" -v "$COHORT":/cohort:ro -v "$HERE":/private:ro $IMG python -B -I /private/check_manifest.py /cohort || fail=1
echo
for id in $(ls "$COHORT/public"); do
  src="$COHORT/public/$id/source"
  [ "${id:0:1}" = b ] && coh=coding-b || coh=coding-c
  acc=$(ls -d "$EVAL/$coh/tasks/${id:1:2}"-*)/acceptance
  row=$("${RUN[@]}" -v "$HERE":/private:ro $IMG python -c "import json,sys;r=[x for x in json.load(open('/private/expectations.json')) if x['id']=='$id'][0];print(r['kind'],r['expected'])")
  kind=${row% *}
  echo "=== $id kind=$kind expected=${row#* } origin=$coh/$(basename "$(dirname "$acc")")"
  a=$("${RUN[@]}" -v "$src":/workspace:ro -v "$acc":/acceptance:ro -w /workspace $IMG python -B -I /acceptance/check.py 2>&1); arc=$?
  echo "acceptance: exit $arc | $(echo "$a" | grep -v '^\s*$' | tail -1 | cut -c1-240)"
  t=$("${RUN[@]}" -v "$src":/workspace:ro -w /tmp $IMG sh -c 'cp -r /workspace /tmp/w && cd /tmp/w && python -m unittest discover 2>&1'); trc=$?
  echo "own tests: exit $trc | $(echo "$t" | grep -E '^Ran |^OK|^FAILED|NO TESTS' | tr '\n' ' ')"
  r=$("${RUN[@]}" -v "$src":/workspace:ro -w /tmp $IMG sh -c 'cp -r /workspace /tmp/w && cd /tmp/w && sed -n "/^\`\`\`sh\$/,/^\`\`\`\$/p" README.md | sed "1d;\$d" > /tmp/ex.sh && cat /tmp/ex.sh && sh /tmp/ex.sh 2>&1; echo "exit $?"')
  echo "README example: $(echo "$r" | tr '\n' ' ' | cut -c1-400)"
  if [ "$kind" = original ]; then
    d=$("${RUN[@]}" -v "$src":/workspace:ro -v "$HERE":/private:ro -w /tmp $IMG sh -c "cp -r /workspace /tmp/w && cd /tmp/w && python -B /private/demos.py $id 2>&1"); drc=$?
    echo "demo: $(echo "$d" | tr '\n' ' ' | cut -c1-600)"
    c=$("${RUN[@]}" -v "$EVAL":/eval:ro -v "$HERE":/private:ro -w /tmp $IMG sh -c "python -B /private/materialize_clean.py /eval $id /tmp/w && cd /tmp/w && python -B /private/demos.py $id 2>&1"); crc=$?
    echo "demo on unseeded variant: exit $crc | $(echo "$c" | tr '\n' ' ' | cut -c1-400)"
    [ $crc -eq 1 ] || { echo "demo does not discriminate"; fail=1; }
    if [ $arc -ne 0 ] || [ $drc -eq 0 ]; then echo "VERDICT: seeded defect verified (acceptance $([ $arc -ne 0 ] && echo fails || echo passes); demo $([ $drc -eq 0 ] && echo demonstrated || echo not-demonstrated))"; else echo "VERDICT: NOT VERIFIED"; fail=1; fi
  else
    rex=$(echo "$r" | tail -1)
    if [ $arc -eq 0 ] && [ $trc -eq 0 ] && [ "$rex" = "exit 0" ]; then echo "VERDICT: control verified (acceptance, own tests and README example pass)"; else echo "VERDICT: NOT VERIFIED"; fail=1; fi
  fi
  echo
done
echo "OVERALL: $([ $fail -eq 0 ] && echo ALL CASES VERIFIED || echo FAILURES PRESENT)"
} > "$OUT" 2>&1
cat "$OUT"
exit $fail
