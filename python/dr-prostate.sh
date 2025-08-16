#!/bin/bash
# DR-Prostate CLI 실행 스크립트

# 스크립트가 있는 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화 (존재하는 경우)
if [ -f "../env/bin/activate" ]; then
    source ../env/bin/activate
fi

# Python CLI 실행
../env/bin/python prostate_cli.py "$@"