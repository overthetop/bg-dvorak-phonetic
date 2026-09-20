# Diagnostic validation

Native Ubuntu 24.04 x86_64 fixture runs with CPython 3.14.7. Destinations are temporary copies of distro XKB data; user ownership
is injected for these fixtures only. Production Linux requires system scope.
Actual xkbcli compile-keymap validates candidates
and installed fixture files. No live keyboard settings were changed.
Paths are sanitized.

### fresh install

```text
2026-09-19T07:18:30.549679+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:30.551836+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:30.577376+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | inspect | health=absent activation=pending
2026-09-19T07:18:30.583665+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | plan | action=install; changes=3
2026-09-19T07:18:30.583695+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | authorize | Apply install in user scope
2026-09-19T07:18:30.583729+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | backup | Recoverable originals will be retained at <fixture>/state/eaa573f7-9bf9-4a23-b143-d136b835367a
2026-09-19T07:18:30.583751+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | validate-staged | Validate supplied candidates before replacing installed content
2026-09-19T07:18:30.583765+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | apply | Apply authorized scoped transaction
2026-09-19T07:18:30.750748+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | verify-installed | Native validation and manifest checks passed
2026-09-19T07:18:30.750813+00:00 | eaa573f7-9bf9-4a23-b143-d136b835367a | INFO | complete | action=installed activation=pending
action=installed activation=pending
```

### current invocation 1

```text
2026-09-19T07:18:30.750908+00:00 | cf9f3b3f-aa9e-4cd0-ae86-1139b45b845d | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:30.754564+00:00 | cf9f3b3f-aa9e-4cd0-ae86-1139b45b845d | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:30.777001+00:00 | cf9f3b3f-aa9e-4cd0-ae86-1139b45b845d | INFO | inspect | health=current activation=pending
2026-09-19T07:18:30.781663+00:00 | cf9f3b3f-aa9e-4cd0-ae86-1139b45b845d | INFO | plan | action=noop; changes=0
2026-09-19T07:18:30.781684+00:00 | cf9f3b3f-aa9e-4cd0-ae86-1139b45b845d | INFO | complete | Already current
action=unchanged activation=pending
```

### current invocation 2

```text
2026-09-19T07:18:30.781716+00:00 | 8cd2e114-2c66-4723-a089-44c4f2e8ea0b | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:30.783577+00:00 | 8cd2e114-2c66-4723-a089-44c4f2e8ea0b | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:30.808900+00:00 | 8cd2e114-2c66-4723-a089-44c4f2e8ea0b | INFO | inspect | health=current activation=pending
2026-09-19T07:18:30.812959+00:00 | 8cd2e114-2c66-4723-a089-44c4f2e8ea0b | INFO | plan | action=noop; changes=0
2026-09-19T07:18:30.812984+00:00 | 8cd2e114-2c66-4723-a089-44c4f2e8ea0b | INFO | complete | Already current
action=unchanged activation=pending
```

### current invocation 3

```text
2026-09-19T07:18:30.813017+00:00 | 42176116-8fd9-40da-b0cb-66acb385c951 | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:30.814844+00:00 | 42176116-8fd9-40da-b0cb-66acb385c951 | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:30.840206+00:00 | 42176116-8fd9-40da-b0cb-66acb385c951 | INFO | inspect | health=current activation=pending
2026-09-19T07:18:30.845500+00:00 | 42176116-8fd9-40da-b0cb-66acb385c951 | INFO | plan | action=noop; changes=0
2026-09-19T07:18:30.845524+00:00 | 42176116-8fd9-40da-b0cb-66acb385c951 | INFO | complete | Already current
action=unchanged activation=pending
```

### legacy update

```text
2026-09-19T07:18:30.845668+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:30.847614+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:30.872509+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | inspect | health=outdated activation=pending
2026-09-19T07:18:30.876889+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | plan | action=update; changes=1
2026-09-19T07:18:30.876911+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | authorize | Apply update in user scope
2026-09-19T07:18:30.876931+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | backup | Recoverable originals will be retained at <fixture>/state/a546f5e2-9647-4eaa-afec-70ecdb243c3e
2026-09-19T07:18:30.876942+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | validate-staged | Validate supplied candidates before replacing installed content
2026-09-19T07:18:30.876950+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | apply | Apply authorized scoped transaction
2026-09-19T07:18:30.979283+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | verify-installed | Native validation and manifest checks passed
2026-09-19T07:18:30.979400+00:00 | a546f5e2-9647-4eaa-afec-70ecdb243c3e | INFO | complete | action=updated activation=pending
action=updated activation=pending
```

### missing registration repair

```text
2026-09-19T07:18:30.980108+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:30.987978+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:31.022635+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | inspect | health=repairable activation=pending
2026-09-19T07:18:31.027142+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | plan | action=repair; changes=1
2026-09-19T07:18:31.027163+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | authorize | Apply repair in user scope
2026-09-19T07:18:31.027185+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | backup | Recoverable originals will be retained at <fixture>/state/f22f18a1-ded4-4a35-9e84-60ff2976583e
2026-09-19T07:18:31.027195+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | validate-staged | Validate supplied candidates before replacing installed content
2026-09-19T07:18:31.027203+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | apply | Apply authorized scoped transaction
2026-09-19T07:18:31.138375+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | verify-installed | Native validation and manifest checks passed
2026-09-19T07:18:31.138437+00:00 | f22f18a1-ded4-4a35-9e84-60ff2976583e | INFO | complete | action=repaired activation=pending
action=repaired activation=pending
```

### Unsafe XML refusal

```text
2026-09-19T07:18:31.138658+00:00 | e2556cfd-ca75-4241-9df6-8cdaef61a30d | INFO | preflight | platform=linux scope=user
2026-09-19T07:18:31.142546+00:00 | e2556cfd-ca75-4241-9df6-8cdaef61a30d | INFO | inspect | Inspect installation and pending recovery
2026-09-19T07:18:31.146743+00:00 | e2556cfd-ca75-4241-9df6-8cdaef61a30d | ERROR | failed | Malformed or ambiguous shared XML registry | operation=installation | cause=no element found: line 1, column 8 | next=Restore the distro registry, then retry.
exit=4
```
