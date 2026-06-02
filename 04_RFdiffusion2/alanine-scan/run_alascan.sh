#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DDG_ROOT="${1:-${SCRIPT_DIR}/ddg_files}"
JOBS="${2:-4}"
STATUS_DIR="${SCRIPT_DIR}/.alascan_status_$(date +%Y%m%d_%H%M%S)"

mkdir -p "${STATUS_DIR}"

run_one_dir() {
	local ddg_dir="$1"
	local dir_name
	local out_dir
	local joblist
	local logfile
	local status

	dir_name="$(basename "${ddg_dir}")"
	out_dir="${ddg_dir}/ddg_out"
	mkdir -p "${out_dir}"

	if [[ -f "${ddg_dir}/ddg_out/job.list" ]]; then
		joblist="${ddg_dir}/ddg_out/job.list"
	elif [[ -f "${ddg_dir}/job.list" ]]; then
		joblist="${ddg_dir}/job.list"
	else
		echo "[ERROR] ${dir_name}: job.list not found" >&2
		touch "${STATUS_DIR}/${dir_name}.fail"
		return 2
	fi

	logfile="${out_dir}/run.log"

	(
		set -euo pipefail
		cd "${ddg_dir}"

		while IFS= read -r cmd || [[ -n "${cmd}" ]]; do
			[[ -z "${cmd// }" ]] && continue
			[[ "${cmd}" =~ ^# ]] && continue
			bash -lc "${cmd}"
		done < "${joblist}"

		shopt -s nullglob
		for pattern in "*.ddg" "*.pdb" "score*" "*.out" "*.sc" "*.fasc" "*.silent"; do
			for f in ${pattern}; do
				[[ "${f}" == "job.list" ]] && continue
				mv -f -- "${f}" "${out_dir}/"
			done
		done
	) >> "${logfile}" 2>&1

	status=$?
	if [[ ${status} -eq 0 ]]; then
		echo "[OK] ${dir_name}"
		touch "${STATUS_DIR}/${dir_name}.ok"
	else
		echo "[FAIL] ${dir_name}, see ${logfile}" >&2
		touch "${STATUS_DIR}/${dir_name}.fail"
	fi
	return ${status}
}

if [[ ! -d "${DDG_ROOT}" ]]; then
	echo "[ERROR] DDG root not found: ${DDG_ROOT}" >&2
	exit 1
fi

DDG_ROOT="$(cd "${DDG_ROOT}" && pwd)"

mapfile -t DDG_DIRS < <(find "${DDG_ROOT}" -mindepth 1 -maxdepth 1 -type d -name "ddg_*" | sort)
if [[ ${#DDG_DIRS[@]} -eq 0 ]]; then
	echo "[ERROR] No ddg_* directories found under ${DDG_ROOT}" >&2
	exit 1
fi

echo "[INFO] Root: ${DDG_ROOT}"
echo "[INFO] Directories: ${#DDG_DIRS[@]}"
echo "[INFO] Parallel jobs: ${JOBS}"

export STATUS_DIR
export -f run_one_dir

parallel_status=0
parallel --no-notice -j "${JOBS}" run_one_dir ::: "${DDG_DIRS[@]}" || parallel_status=$?

ok_count=$(find "${STATUS_DIR}" -type f -name "*.ok" | wc -l)
fail_count=$(find "${STATUS_DIR}" -type f -name "*.fail" | wc -l)

echo "[SUMMARY] success=${ok_count} fail=${fail_count}"
if [[ ${fail_count} -gt 0 ]]; then
	echo "[FAILED DIRS]"
	find "${STATUS_DIR}" -type f -name "*.fail" -printf "%f\n" | sed 's/\.fail$//' | sort
fi

if [[ ${parallel_status} -ne 0 || ${fail_count} -gt 0 ]]; then
	exit 1
fi