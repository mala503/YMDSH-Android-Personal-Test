#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_root="$(cd "$project_root/../.." && pwd)"
toolchains="$workspace_root/.ymdsh-toolchains"

export JAVA_HOME="$toolchains/jdk-17.0.20.1+1"
export ANDROID_HOME="$toolchains/sdk"
export ANDROID_SDK_ROOT="$toolchains/sdk"
export GRADLE_USER_HOME="$toolchains/gradle-cache"
export YMDSH_MAVEN_BRIDGE='http://127.0.0.1:19766'

python3 -B "$project_root/tools/ymdsh_maven_bridge.py" 19766 &
bridge_pid=$!
trap 'kill "$bridge_pid" 2>/dev/null || true' EXIT

"$toolchains/gradle-9.3.1/bin/gradle" --project-dir "$project_root" \
  -Dorg.gradle.internal.http.socketTimeout=180000 \
  -Dorg.gradle.internal.http.connectionTimeout=120000 "$@"
