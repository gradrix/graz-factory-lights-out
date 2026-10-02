# Can a local browser reach only its disposable application?

Type: prototype
Status: feasibility resolved; product implementation and qualification pending
Decision maker: agent, under the user-authorized browser/environment destination

The rig prototype demonstrated an owned app binding loopback in a network-none namespace, with the browser joining that exact namespace. App access passed; gateway/LAN/Internet attempts returned ENETUNREACH. Nonroot Chromium with sandbox enabled required a one-rule seccomp adaptation: allow chroot without requiring the dropped outer CAP_SYS_CHROOT. Independent assessment confirmed the structural delta and retained kernel privilege checks. Actual renderer namespace/seccomp facts were captured after a reporter-only correction. No added capability, no-sandbox fallback or host configuration change was used.

Route for the later browser slice: reproduce these pins/boundary with supervised lifecycle, explicit resource/artifact bounds and realistic app journeys. Do not substitute an internal bridge as proof of host isolation. Do not claim public browsing is covered. Private shm sizing remains unmeasured because the prototype's default browser arguments used temporary storage instead.

Evidence: ../browser-boundary-prototype.md. Full Stage4 acceptance remains ten research answers and five app journeys plus negative controls. Approved document evidence remains the only active maintained-code unit.
