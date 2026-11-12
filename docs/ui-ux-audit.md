# ToolX UI/UX audit and improvements

Reviewed 11 November 2026 using [Hallmark v2](https://github.com/nutlope/hallmark/tree/04977e15f3dfd6ee4b74c887dac3eb52665d6c92/skills/hallmark), with the existing Django application as the source of product facts. Scope: marketing pages, account/recovery screens, dashboard, histories, editors, previews and profile.

## Findings and changes

| Finding | User impact | Change |
| --- | --- | --- |
| Navigation hidden below the desktop breakpoint; unlabeled icons | Mobile users lose workspace destinations; icons have weak accessible names | Labeled navigation at every size, current-page indication, native Create disclosure, POST logout |
| Login omits non-field errors; ineffective remember checkbox | Failed login has no visible explanation; checkbox promises unsupported behavior | Visible alert for authentication errors, preserved return destination, removed nonfunctional checkbox |
| Password help hidden in CSS | Signup rules are difficult to discover | Persistent guidance with labels and error associations |
| Coral controls have approximately 2.77:1 white-text contrast | Functional labels are hard to read | Darker coral for controls/links, visible focus, field-edge contrast, hover/active/disabled states |
| Fixed viewport auth layouts and narrow Bootstrap columns | Small screens and longer content are constrained | Capped containers, wrapping navigation, stacking forms, flexible document rows |
| Empty histories show no next action | First-time users lack direction | Real empty states linking to the corresponding editor |
| Nested buttons inside links; HTML title contains pagination | Ambiguous keyboard interaction and malformed semantics | Native links styled as actions; pagination remains in the history body |
| Account and workspace screens use inconsistent layouts | Recovery, editing and navigation feel disconnected | Shared workspace, account, field and status patterns |
| Unstructured letter preview loses line breaks | Copy is harder to review before export | Readable document measure, preserved line breaks and CTA emphasis, contextual download links |
| Duplicated error IDs and misaligned profile grid found during independent review | Error references are ambiguous; profile pairs fall into wrong columns | One Django-owned error ID per field, semantic label/value grid, regression coverage |

## System and scope

Brand mode retains the original Lato face, warm paper and coral/navy family; it does not introduce a randomly selected theme. The accent is reserved for primary actions and links. `tokens.css` owns the colors, typography, spacing and motion values. The interface uses native browser controls and remains usable without JavaScript; the former Bootstrap, jQuery, Popper and Font Awesome runtime assets are no longer required. Existing image/logo assets are retained, with no invented metrics, testimonials, prices or product features.

The principal task is writing and revisiting copy. Dashboard summaries use compact document rows; editors retain every field and keep submission explicit. Content saves only when a real POST succeeds. No fake autosave, synthetic loading result, billing flow, or destructive action was added. Server-rendered screens use real empty, populated, invalid and successful states; there is no asynchronous fetch layer to simulate.

Copy was tightened around the same functionality: “Fill out the boxes…” becomes “Write a sales letter”; the malformed article instruction becomes “Write an article draft”; “Email / AdCopies has been generated” becomes a saved-work confirmation. Login and account actions use consistent wording. The full source diff records every copy change; activation and reset notices retain their non-enumerating meaning.

## Preservation and verification

- Compared 25 Django-rendered states before/after: all 53 original named-field occurrences and 233 original link destinations remain present (paths normalized for trailing slashes). Global creation shortcuts remain available. No routes or files were deleted.
- Forms retain CSRF tokens, POST methods, IDs used for submission, profile multipart encoding, disabled email behavior and server validation. Preview/export ownership checks are unchanged.
- Removed UI exceptions: the unnamed remember checkbox never changed a session; decorative third-party runtime scripts were replaced by native navigation and text labels. The static field helper relies on Django’s own accessible error IDs.
- 38 Django tests pass, covering login feedback and destination, signup guidance/error associations, editor fields, empty-state destinations, safe preview content, uploads and existing account/export security behavior.
- Hallmark static audit of the shared stylesheet: before 48 Floor findings and 6 Reflex findings; after 0 Floor, 0 Reflex and 0 warnings. Resolved page audits use actual Django HTML with the shared CSS inlined because the linter cannot follow Django template inheritance.
- Resolved-page warnings about long control labels include visually hidden document titles used to distinguish repeated export/edit links for screen readers. The visible controls have short labels; forcing all those labels onto one line would damage the mobile layout. These are reviewed false positives. Recovery notices retain their existing apostrophes rather than rewriting transactional meaning.
- Local Chromium rendering is blocked by this workspace’s Unix-socket restrictions. No local screenshot, responsive-render, contrast-render or visual finish pass is claimed. An independent static review identified and resolved four concrete defects but correctly withheld its visual verdict.
- GitHub’s browser job runs real Chrome on 14 screens at widths 320, 375, 768, 1280, 1440 and 1920, checks overflow, runs axe WCAG A/AA audits at mobile/desktop sizes, and uploads screenshots and its report. Its result is the browser evidence; confirm it on the pull request before merging. Automated accessibility checks do not replace manual screen-reader and visual review.

## Remaining review

Inspect the CI screenshots for visual balance, keyboard-test the native disclosure and forms, and check the interface with a screen reader. Live mail delivery, S3 uploads, exposed-credential resets and GitHub Support’s historical-data purge remain separate operational work described in README. This redesign does not deploy a service or change production accounts.
