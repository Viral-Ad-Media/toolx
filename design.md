# ToolX interface system

This system preserves the existing ToolX brand and the Django application's writing workflows. It was established in the Hallmark UI review, recorded in `docs/ui-ux-audit.md`.

- Palette: warm paper, navy text/navigation and coral signals. Functional coral is darker than the original decorative coral to meet contrast requirements. Exact roles live in `static/css/tokens.css`.
- Typography: Lato at 400/700, with readable native sans fallbacks; fixed app heading scale and a larger marketing heading.
- Navigation: labeled top navigation on all screen sizes, visible current destination, native Create disclosure and CSRF-protected POST logout. Mobile controls wrap; nothing essential is desktop-only.
- Containers: one centered 1184px maximum with responsive gutters. At 640px, account panels and profile definitions stack; document actions wrap. Editors collapse to one column below 960px.
- Controls: 44px minimum hit targets, one coral primary treatment, quiet secondary actions, visible keyboard focus, disabled states with native semantics, no decorative animation.
- Forms: visible labels and required indicators; help and errors associated with one unique ID per field. Validation and save results come from Django. No fake autosave or remember-session control.
- Content: real empty, populated, invalid and saved states. Document titles wrap, letter previews preserve line breaks and CTA emphasis, history pagination stays in the URL.
- Components: `base.html`, `app_base.html`, `nav.html`, `field.html`, document-row partials and `pagination.html`; no frontend framework migration or client-side routing.
- Material: existing logos/illustrations and real user content. Demo records in browser checks use a disposable database and are never product claims.
