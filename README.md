# GFLO — local-first software factory

GFLO is an independent, staged experiment in autonomous software production with small-context local models. Most of the factory remains a research and implementation plan, not a finished runtime.

- [Model-serving launcher](infra/serving/README.md): use an existing local endpoint, explicitly configure a remote endpoint, or manage a pinned SGLang container on an NVIDIA host.
- [Planning map](.scratch/local-lights-out-factory/map.md)
- [GPU handoff](.scratch/local-lights-out-factory/HANDOFF.md)
- [Proposed staged implementation](.scratch/local-lights-out-factory/issues/12-plan-the-staged-implementation-and-validation.md)

Run dependency-launcher checks without a GPU:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/serve.py config
```

SFLO and Gas City are architectural references only. No automatic cloud fallback is included. Real-model coding capability and RTX 5090 operation have not yet been validated in this repository.
