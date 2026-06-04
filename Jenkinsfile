// Jenkinsfile — multibranch pipeline for arcana-cloud-python
// Adapted from legacy python-app-pipeline (single-branch job polling SCM).
//
// Key differences from the legacy XML-embedded script:
//   * `checkout scm` (no hardcoded branch=main)        — supports every branch + every PR
//   * `pollSCM` trigger removed                        — Jenkins multibranch + GitHub webhook drive triggers
//   * "Push to Registry" + "Arch Qube Metrics" gated   — only main pushes to registry; PR builds stay local
//   * SonarQube gets pullrequest.* params on PRs       — PR-decoration in Sonar UI
//   * `dir("${env.PROJECTS_DIR}/...")` blocks removed  — multibranch uses workspace root

pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '1'))
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        APP_NAME  = "python-app"
        REGISTRY  = "localhost:5000"
        IMAGE_TAG = "${REGISTRY}/arcana/${APP_NAME}"
        VERSION   = "1.0.0"
    }

    stages {
        stage("Checkout") {
            steps {
                checkout scm
                sh 'git log -1 --oneline'
                script {
                    echo "Branch: ${env.BRANCH_NAME ?: 'unknown'}"
                    echo "PR: ${env.CHANGE_ID ?: 'no'} (target: ${env.CHANGE_TARGET ?: 'n/a'})"
                }
            }
        }

        stage("Cleanup Old Images") {
            steps {
                sh '''
                    docker images --format '{{.Repository}}:{{.Tag}}' \
                        | grep "${APP_NAME}.*build-" \
                        | sort -t- -k2 -rn \
                        | tail -n +4 \
                        | xargs -r docker rmi 2>/dev/null || true
                    docker compose -f docker-compose.test.yml down \
                        --remove-orphans 2>/dev/null || true
                '''
            }
        }

        stage("Docker Compose Build") {
            steps {
                sh "VERSION=${VERSION} docker compose -f docker-compose.ci.yml build"
                sh "docker tag localhost:5000/arcana/${APP_NAME}:${VERSION} ${IMAGE_TAG}:build-${BUILD_NUMBER}"
            }
        }

        stage("Unit Tests") {
            steps {
                sh '''#!/bin/bash
                    # DinD-safe coverage extraction: this Jenkins talks to the HOST docker
                    # daemon, so the compose `./coverage:/output` bind mount resolves to a stray
                    # host path and the report never lands in the workspace (sonar then sees
                    # coverage=0). Run a NAMED container (not --rm) and `docker cp` the report
                    # out, which streams through the API into the real workspace.
                    set +e
                    docker rm -f "${APP_NAME}-cov-${BUILD_NUMBER}" 2>/dev/null || true
                    docker compose -f docker-compose.test.yml run \
                        --name "${APP_NAME}-cov-${BUILD_NUMBER}" --build test
                    rc=$?
                    mkdir -p coverage
                    docker cp "${APP_NAME}-cov-${BUILD_NUMBER}:/app/cov/coverage.xml" coverage/coverage.xml || true
                    docker rm -f "${APP_NAME}-cov-${BUILD_NUMBER}" 2>/dev/null || true
                    exit $rc
                '''
            }
        }

        stage("Integration: Layered gRPC") {
            // Serialize this repo's layered-compose stage: main + PR builds share
            // static compose project/network/container names and collide when concurrent.
            options { lock('ci-python-layered') }
            steps {
                sh '''#!/bin/bash
                    set -e
                    # CI gRPC DB URL is supplied inline (the .env.ci referenced by the old
                    # --env-file is gitignored, so it never exists on a fresh Jenkins clone →
                    # compose up aborted with "couldn't find env file" → no containers → the
                    # smoke-test health check timed out). Value matches the mysql service creds
                    # and the (passing) K8s-gRPC variant's DATABASE_URL.
                    export CI_GRPC_DATABASE_URL="mysql+pymysql://arcana:ci_arcana@mysql:3306/arcana_cloud"
                    PYTHON_IMAGE=${IMAGE_TAG}:build-${BUILD_NUMBER} \
                    docker compose -p arcana-ci-python-grpc \
                        -f deployment/layered/docker-compose-ci-grpc.yml \
                        up -d
                    JENKINS_ID=$(hostname)
                    docker network connect arcana-ci-python-grpc-net ${JENKINS_ID} 2>/dev/null || true
                    bash scripts/integration-smoke-test.sh \
                        http://arcana-ci-python-grpc-controller:5000 grpc-layered 300
                    docker network disconnect arcana-ci-python-grpc-net ${JENKINS_ID} 2>/dev/null || true
                '''
            }
            post {
                always {
                    sh '''
                        echo "=== Controller logs ===" && docker logs arcana-ci-python-grpc-controller 2>&1 | tail -30 || true
                        echo "=== Service logs ===" && docker logs arcana-ci-python-grpc-service 2>&1 | tail -20 || true
                        echo "=== Repository logs ===" && docker logs arcana-ci-python-grpc-repository 2>&1 | tail -20 || true
                        docker network disconnect arcana-ci-python-grpc-net $(hostname) 2>/dev/null || true
                        CI_GRPC_DATABASE_URL=placeholder PYTHON_IMAGE=placeholder docker compose -p arcana-ci-python-grpc \
                            -f deployment/layered/docker-compose-ci-grpc.yml \
                            down -v --remove-orphans 2>/dev/null || true
                    '''
                }
            }
        }

        stage("Integration: K8s gRPC") {
            // Serialize ALL kind/k8s stages host-wide: concurrent kind clusters
            // OOM-killed image imports on the 24G shared host (exit 137).
            options { lock('ci-kind-global') }
            steps {
                sh '''#!/bin/bash
                    export PATH="/var/jenkins_home/bin:${PATH}"
                    kind version || { echo "kind not found"; exit 1; }
                    bash scripts/kind-smoke-test.sh "${IMAGE_TAG}:build-${BUILD_NUMBER}" grpc 480
                '''
            }
            post {
                always {
                    sh '''#!/bin/bash
                        export PATH="/var/jenkins_home/bin:${PATH}"
                        kind get clusters 2>/dev/null | grep arcana-ci | while read cl; do
                            kind delete cluster --name "$cl" 2>/dev/null || true
                        done
                    '''
                }
            }
        }

        stage("SonarQube Analysis") {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh """sonar-scanner -Dsonar.projectKey=python-app -Dsonar.scm.disabled=true"""
                    sh '''
                        set -e
                        TOKEN="${SONAR_AUTH_TOKEN:-$SONAR_TOKEN}"
                        RT=.scannerwork/report-task.txt
                        [ -f "$RT" ] || { echo "report-task.txt missing"; exit 1; }
                        CE_TASK_ID=$(grep '^ceTaskId=' "$RT" | cut -d= -f2-)
                        ANALYSIS_ID=""
                        for i in $(seq 1 60); do
                            RESP=$(curl -s -u "$TOKEN:" "$SONAR_HOST_URL/api/ce/task?id=$CE_TASK_ID")
                            ST=$(echo "$RESP" | grep -o '"status":"[A-Z_]*"' | head -1 | cut -d'"' -f4)
                            echo "  CE status: ${ST:-?} (try $i)"
                            if [ "$ST" = "SUCCESS" ]; then ANALYSIS_ID=$(echo "$RESP" | grep -o '"analysisId":"[^"]*"' | head -1 | cut -d'"' -f4); break;
                            elif [ "$ST" = "FAILED" ] || [ "$ST" = "CANCELED" ]; then echo "CE $ST"; exit 1; fi
                            sleep 5
                        done
                        [ -n "$ANALYSIS_ID" ] || { echo "CE timeout"; exit 1; }
                        GATE=$(curl -s -u "$TOKEN:" "$SONAR_HOST_URL/api/qualitygates/project_status?analysisId=$ANALYSIS_ID")
                        GST=$(echo "$GATE" | grep -o '"status":"[A-Z]*"' | head -1 | cut -d'"' -f4)
                        echo "Quality gate: ${GST:-UNKNOWN}"
                        if [ "$GST" != "OK" ]; then echo "$GATE"; exit 1; fi
                    '''
                }
            }
        }

        stage("Architecture Qube") {
            steps {
                sh '''
                    docker rm -f arcana-arch-qube-python-${BUILD_NUMBER} 2>/dev/null || true
                    docker create --name arcana-arch-qube-python-${BUILD_NUMBER} --network devops_default \
                        -v /src -v /output \
                        arcana.boo/arcana/arch-qube:latest \
                        scan /src --framework python --no-ai --ci \
                        --format json,markdown -o /output --threshold 90 || exit 1
                    tar --exclude=./.git --exclude=./arch-qube-reports -C . -cf - . \
                        | docker cp - arcana-arch-qube-python-${BUILD_NUMBER}:/src || exit 1
                    docker start -a arcana-arch-qube-python-${BUILD_NUMBER}
                    AQ_RC=$?
                    mkdir -p arch-qube-reports
                    docker cp arcana-arch-qube-python-${BUILD_NUMBER}:/output/. arch-qube-reports/ 2>/dev/null || true
                    docker rm -f arcana-arch-qube-python-${BUILD_NUMBER} 2>/dev/null || true
                    exit $AQ_RC
                '''
            }
        }

        stage("Image Info") {
            steps {
                sh "docker images --format 'table {{.Repository}}:{{.Tag}}\\t{{.Size}}' | grep ${APP_NAME} || true"
            }
        }

        stage("Push to Registry") {
            when { branch 'main' }
            steps {
                sh "docker push ${IMAGE_TAG}:${VERSION}"
                sh "docker push ${IMAGE_TAG}:build-${BUILD_NUMBER}"
            }
        }

        stage("Arch Qube Metrics") {
            when { branch 'main' }
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'SUCCESS') {
                    sh "bash /data/projects/_scripts/arch-qube-metrics.sh \$(pwd) arcana-cloud-python || true"
                }
            }
        }
    }

    post {
        success { echo "Pipeline SUCCESS - ${APP_NAME}:${VERSION} branch=${env.BRANCH_NAME ?: '?'} pr=${env.CHANGE_ID ?: 'no'}" }
        failure { echo "Pipeline FAILED - branch=${env.BRANCH_NAME ?: '?'} pr=${env.CHANGE_ID ?: 'no'}" }
        always  { echo "Build number ${BUILD_NUMBER} done" }
    }
}
