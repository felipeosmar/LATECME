# Remove Unused Static File Plugins to Reduce Deployment Size

## Overview

The staticfiles/plugins directory contains ~50MB of unused JavaScript libraries (DataTables extensions, CKEditor, Flot charts, etc.) that were likely part of an admin template. The actual application only uses Tabler, HTMX, and Alpine.js which are in static/vendor/.

## Rationale

Large static file directories slow down `collectstatic`, increase deployment image size, and waste storage. The unused plugins also pose security risks if they contain outdated vulnerable code. The base template confirms only Tabler/HTMX/Alpine are loaded.

---
*This spec was created from ideation and is pending detailed specification.*
