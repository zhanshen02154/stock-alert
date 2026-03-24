pipeline {
	agent any
	environment {
		DOCKER_IMAGE = '192.168.0.62/agent/stock-alert'
		DOCKER_TAG = "${env.GIT_BRANCH}-${env.GIT_COMMIT.substring(0, 8)}"
	}
	stages {
		stage('Build and Push Docker Image') {
			when {
				anyOf {
					branch 'dev'
					expression { return env.TAG_NAME != null }
				}
			}
			steps {
				script {
					if (env.TAG_NAME) {
						DOCKER_TAG = "${env.TAG_NAME}"
					}
					sh 'set +x'
					docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
					docker.withRegistry('https://192.168.0.62', 'harbor-jenkins') {
					    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                    }
                    sh "docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG}"
				}
			}
		}
		stage('Deploy to Kubernetes') {
			when {
				anyOf {
					branch 'dev'
					expression { return env.TAG_NAME != null }
				}
			}
			steps {
				script {
					try {
						withCredentials([string(credentialsId: 'kubernetes-api-server', variable: 'k8s_api_server')]) {
							withKubeConfig([credentialsId: 'kubernetes-config', serverUrl: "$k8s_api_server", namespace: 'dev']) {
								sh """
								set +x
								/usr/bin/kubectl set image deployment/stock-alert stock-alert-container=${DOCKER_IMAGE}:${DOCKER_TAG} -n dev --record
								/usr/bin/kubectl rollout status deployment/stock-alert -n dev --timeout 360s
								"""
							}
						}
					}
					catch(exc) {
						withCredentials([string(credentialsId: 'kubernetes-api-server', variable: 'k8s_api_server')]) {
							withKubeConfig([credentialsId: 'kubernetes-config', serverUrl: "$k8s_api_server", namespace: 'dev']) {
								sh '''
								set +x
								/usr/bin/kubectl rollout undo deployment/stock-alert -n dev
								'''
							}
						}
					}
				}
			}
		}
	}
	post {
		always {
			deleteDir()
		}
		success {
			echo "🎉Pipeline ${DOCKER_IMAGE}:${DOCKER_TAG} deploy succeeded"
		}
		failure {
			echo "❌Pipeline ${DOCKER_IMAGE}:${DOCKER_TAG} deploy failed"
		}
	}
}