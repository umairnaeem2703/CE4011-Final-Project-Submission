Read:

* `docs/final_latex/README.txt`
* `docs/final_latex/main_report/main_report.tex`
* `docs/final_latex/main_report/sections/*.tex`
* `docs/final_latex/user_manual/user_manual.tex`
* `docs/final_latex/verification_appendix/verification_appendix.tex`
* `docs/final_latex/diagrams/plantuml/*.puml`
* `docs/final_latex/diagrams/rendered/*`
* all figure files already placed under `docs/final_latex/`
* `data/test-frame.xml`
* `data/test-modal-flex-beam.xml`
* all static/modal exported result files under `data/`
* available SAP2000/reference result files, if present

Task: Perform the final documentation evidence and table-completion pass.

Scope:

* Documentation only.
* Do not modify source code, tests, XML fixtures, XML schema, UI behavior, or solver math.
* Do not create a new `/screenshots` folder.
* Use the figures already placed in the LaTeX documentation folders.
* Keep figure placements and captions already prepared unless there is a clear LaTeX compile problem.
* Preserve the final submitted scope: Static Analysis + Modal Analysis Tkinter desktop MVP.
* RSA/THA may be mentioned only as deferred/future-extension backend work.
* Preserve the compressed main report page limit.
* Do not invent numerical benchmark values.

Required work:

1. Locate the figures already placed in `docs/final_latex/` and connect them to the existing LaTeX figure placements/captions.
2. Use `\IfFileExists` or equivalent fallback logic so compilation does not fail if a figure is missing.
3. Read the static and modal result export files in `data/`.
4. Fill the verification tables using reliable values from:

   * static/modal exported result files in `data/`,
   * available SAP2000/reference files,
   * existing documented pytest baseline.
5. For unavailable reference values, keep the table row as a clear TODO rather than inventing values.
6. Fill or update tables for:

   * static frame benchmark using `data/test-frame.xml`,
   * modal benchmark using `data/test-modal-flex-beam.xml`,
   * exported static result tables/plots,
   * exported modal result tables/plots,
   * automated pytest validation baseline,
   * desktop XML/export command-path validation.
7. Keep detailed tables in `verification_appendix.tex`.
8. Keep the main report compact; only update its validation summary if needed.
9. Ensure the user manual examples remain based on:

   * `data/test-frame.xml` for Static Analysis,
   * `data/test-modal-flex-beam.xml` for Modal Analysis.
10. Remove resolved TODO placeholders, but leave unresolved TODOs only where evidence or numerical values are genuinely unavailable.

Checks:

* Compile:

  * main report,
  * user manual,
  * installation manual,
  * verification appendix,
  * video script.
* Report changed files, figures inserted, tables filled, unresolved TODOs, compile results, and final page counts in 10 bullets or fewer.
