#!/usr/bin/env bash
# Start a new Python/Flask service product from this repo's full layered skeleton.
#
#   tools/new-app.sh billing ~/Documents/projects/billing
#
# Copies the committed tree (git archive HEAD), so the new product keeps AGENTS.md,
# CLAUDE.md, tools/ (scaffolding + hook + arch-check), the Jenkinsfile and the arch-qube
# gate. Copying single packages into a fresh Flask app loses all of that (AGENTS.md §1).
#
# No --no-demo: the template's only features are User and Auth, and token_required (every
# protected route, including what tools/new-feature.sh generates) depends on AuthService and
# the User model, so there is no demo-only module to drop.
set -euo pipefail

[ $# -eq 2 ] || { echo "usage: $0 <app-name> <dest-dir>" >&2; exit 1; }
APP="$1"
DEST="$2"
[[ "$APP" =~ ^[a-z][a-z0-9]*(-[a-z0-9]+)*$ ]] || { echo "app-name: lower-case letters/digits, words joined by '-' (it becomes compose/k8s/Jenkins/Sonar names)" >&2; exit 1; }
case "$APP" in arcana|arcana-cloud|arcana-cloud-python|python-app) echo "app-name must differ from the template's identities" >&2; exit 1 ;; esac
[ ! -e "$DEST" ] || { echo "$DEST already exists — refusing to overwrite" >&2; exit 1; }
command -v perl >/dev/null || { echo "perl is required" >&2; exit 1; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git -C "$ROOT" diff --quiet HEAD -- AGENTS.md tools/ || echo "note: uncommitted changes in AGENTS.md/tools are NOT copied (git archive HEAD)" >&2

mkdir -p "$DEST"
git -C "$ROOT" archive HEAD | tar -x -C "$DEST"
SRC_SHA="$(git -C "$ROOT" rev-parse --short HEAD)"
APP_US="$(printf '%s' "$APP" | tr '-' '_')"     # MySQL database names
APP_ORG="$(printf '%s' "$APP" | tr -d '-')"      # Docker Hub org placeholder (no dashes allowed)
cd "$DEST"

# ---- Product identity. Every place the template name is load-bearing:
#  1. CI identities on the shared Jenkins host: Jenkins APP_NAME / image + Sonar key
#     "python-app", layered-compose project/network/containers arcana-ci-python-grpc-*,
#     the lock 'ci-python-layered', kind cluster arcana-ci-python-<proto> + namespace
#     arcana-ci-kind-python + its arcana-ci-{config,secrets,controller,service,repository}
#     objects, the post-step "grep arcana-ci" that DELETES every matching kind cluster, and
#     the arch-qube container arcana-arch-qube-python-*. Two products must not share them.
#  2. Runtime names: compose projects/containers/volumes/networks arcana-cloud-*,
#     arcana-network, k8s namespace/labels arcana-cloud, SERVICE_NAME, image arcana-cloud-python,
#     Docker Hub org arcanacloud, database names arcana_cloud / arcana_cloud_test.
# Not renamed on purpose: the Python package `app` (generic import root, not an identity),
# the proto package `arcana` (wire contract compiled into app/grpc_protos/*_pb2.py — renaming
# it means regenerating every stub and breaking existing clients), the database user `arcana`
# (credential, change it with the secrets), and arcana.boo (registry / arch-qube image host).
# tools/, AGENTS.md and CHANGELOG.md are excluded: they describe the template.
FILES="$(grep -rIl --exclude-dir=.git --exclude-dir=tools --exclude-dir=grpc_protos \
    --exclude=AGENTS.md --exclude=CHANGELOG.md \
    -e arcana -e python-app -e 'Python App' -e ci-python-layered . || true)"
[ -n "$FILES" ] || { echo "new-app: no template identities found — wrong source tree?" >&2; exit 1; }
printf '%s\n' "$FILES" | while IFS= read -r f; do
    A="$APP" U="$APP_US" O="$APP_ORG" perl -pi -e '
        s/arcana-ci-python-/$ENV{A}-ci-/g;
        s/arcana-ci-kind-python/$ENV{A}-ci-kind/g;
        s/arcana-ci-(repository|service|controller|config|secrets)\b/$ENV{A}-ci-$1/g;
        s/grep arcana-ci\b/grep $ENV{A}-ci-/g;
        s/arcana-arch-qube-python-/$ENV{A}-arch-qube-/g;
        s/\bci-python-layered\b/$ENV{A}-ci-layered/g;
        s/arcana-cloud-python/$ENV{A}/g;
        s/(?<![\w-])arcana-cloud(?!-(?:springboot|rust|go|nodejs|python)\b)/$ENV{A}/g;
        s/\barcana_cloud/$ENV{U}/g;
        s/\barcanacloud\b/$ENV{O}/g;
        s/\barcana-network\b/$ENV{A}-network/g;
        s/\bpython-app\b/$ENV{A}/g;
        s/Python App/$ENV{A}/g;
    ' "$f"
done

# Fail loudly if a CI/runtime identity survived.
LEFT="$(grep -rInE --exclude-dir=.git --exclude-dir=tools --exclude=AGENTS.md --exclude=CHANGELOG.md \
    'python-app|arcana-cloud-python|arcana-ci-|ci-python-layered|arcana_cloud|arcana-cloud-(base|monolithic|service|controller|repository)' . || true)"
if [ -n "$LEFT" ]; then
    echo "new-app: template identities still present after rename:" >&2
    printf '%s\n' "$LEFT" | head >&2
    exit 1
fi

# ---- Fresh history: version 0.1.0, empty changelog.
rm -f CHANGELOG.md
printf '{\n  ".": "0.1.0"\n}\n' > .release-please-manifest.json

cat >> AGENTS.md <<EOT

## Origin

Created from arcana-cloud-python @ \`${SRC_SHA}\` by \`tools/new-app.sh\` (CI, Sonar, compose,
k8s and database names renamed to \`${APP}\` / \`${APP_US}\`). The layers, rules and definition
of done above apply unchanged. Remove template features you do not need through
\`app/di_container.py\` and \`app/__init__.py\`, not by flattening.
EOT

git init -q
tools/install-hooks.sh >/dev/null
git add -A
# --no-verify only for this import commit: every file counts as "added" here, so the hook
# would judge the template's legacy app/ root modules (Config.py, *_server.py, …) as new
# flat files. The template itself passes arch-check; every later commit in the product goes
# through the hook.
git -c user.name="${GIT_AUTHOR_NAME:-new-app}" -c user.email="${GIT_AUTHOR_EMAIL:-new-app@localhost}" \
    commit -q --no-verify -m "chore: start ${APP} from arcana-cloud-python ${SRC_SHA}"

echo "created $DEST (${APP}) from arcana-cloud-python ${SRC_SHA}; hooks: $(git config core.hooksPath)"
echo "next: cd $DEST && tools/new-feature.sh <Name>   # one vertical slice per feature"
