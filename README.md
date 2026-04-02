# REPEC Plugin for Janeway

Janeway plugin that generates and serves ReDIF metadata endpoints for REPEC archive registration.

[REPEC](https://repec.org) (Research Papers in Economics) is a collaborative effort of hundreds of volunteers to enhance the dissemination of research in economics. Participation requires hosting metadata files in the [ReDIF](http://openlib.org/acmes/root/docu/redif_1.html) (Research Documents Information Format) format on your server. This plugin generates those files dynamically from your Janeway journal data.

## Endpoints

Once installed and configured, the plugin exposes four URLs per journal:

| URL | Description |
|-----|-------------|
| `/plugins/repec/archive.rdf` | `ReDIF-Archive 1.0` — top-level archive metadata |
| `/plugins/repec/series.rdf` | `ReDIF-Series 1.0` — journal series metadata |
| `/plugins/repec/papers/` | Plain-text index of paper URLs (for REPEC crawlers) |
| `/plugins/repec/papers/{id}.rdf` | `ReDIF-Article 1.0` — per-article metadata |

All files are generated dynamically from your journal's published articles. No cron jobs or file storage are required.

## Installation

1. Copy the `repec` directory into your Janeway `src/plugins/` folder.

2. Run migrations:

   ```bash
   python manage.py migrate repec
   ```

3. Install the plugin record:

   ```bash
   python3 manage.py install_plugins repec
   ```

4. Restart your Janeway instance.

## Configuration

Navigate to `/plugins/repec/admin/` on your journal to configure the plugin. You will need:

- **Archive code** — a short code (e.g. `sur`) assigned to your institution by REPEC. Apply at [ideas.repec.org/archives.html](https://ideas.repec.org/archives.html).
- **Series code** — a 6-character code you propose when registering (e.g. `surrec`). Conventionally `{archive_code}{journal_abbrev}`.
- **Maintainer email** — the address REPEC will use to report errors.

Once saved, the admin page shows the live URLs to submit to REPEC.

## Registering with REPEC

1. Obtain an archive code from REPEC at [ideas.repec.org/archives.html](https://ideas.repec.org/archives.html).
2. Enter your codes in the plugin settings.
3. Submit your `archive.rdf` URL to REPEC for harvesting.

See the [REPEC step-by-step guide](https://ideas.repec.org/stepbystep.html) for full registration instructions.

## Handle format

Article handles follow the Appendix C suggestion from the ReDIF spec:

```
RePEC:{archive}:{series}:v:{volume}:y:{year}:i:{issue}:p:{start}-{end}
```

When an article has no page numbers, the article's database ID is used as the item number instead:

```
RePEC:{archive}:{series}:v:{volume}:y:{year}:i:{issue}:{id}
```

## Requirements

- Janeway 1.7+
