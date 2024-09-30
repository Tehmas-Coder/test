pipeline {
    agent any

    parameters {
        string(name: 'BRANCH', defaultValue: 'main', description: 'Git Branch to deploy')
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'], description: 'Environment to deploy')
    }

    environment {
        // Since the server IP is the same for all environments, we still use the same IP for all environments.
        DJANGO_EC2_IP = 'ec2-54-216-182-84.eu-west-1.compute.amazonaws.com'
        SHELL_SCRIPT_PATH=/var/lib/jenkins/workspace/my-psychometric-exam/scripts/pipeline.sh
        SLACK_WEBHOOK_URL = credentials('slack-webhook-url')
    }

    stages {
        stage('Checkout Code') {
            steps {
                // Check out the code from the my-psychometric-exam repository
                checkout([$class: 'GitSCM', branches: [[name: "*/${params.BRANCH}"]],
                          userRemoteConfigs: [[url: 'https://github.com/your-repo/my-psychometric-exam.git',
                                               credentialsId: 'github-token']]])
            }
        }

        stage('Deploy to Server') {
            steps {
                script {
                    // Use SSH credentials to connect to the server and run the deployment script
                    sshagent(['django-ec2-ssh-key']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@${DJANGO_EC2_IP} 'bash ${SHELL_SCRIPT_PATH} ${params.ENVIRONMENT}'
                        """
                    }
                }
            }
        }

        stage('Notify Slack: Deployment Started') {
            steps {
                script {
                    // Notify Slack that the deployment has started
                    sh """
                        curl -X POST -H 'Content-type: application/json' --data '{"text":"Deployment started for branch ${params.BRANCH} in ${params.ENVIRONMENT} environment for my-psychometric-exam."}' ${SLACK_WEBHOOK_URL}
                    """
                }
            }
        }
    }

    post {
        always {
            cleanWs() // Clean up workspace after every build
        }

        success {
            script {
                // Send a success notification to Slack using the webhook
                sh """
                    curl -X POST -H 'Content-type: application/json' --data '{"text":"Branch ${params.BRANCH} successfully deployed to ${params.ENVIRONMENT} environment for my-psychometric-exam."}' ${SLACK_WEBHOOK_URL}
                """
            }
        }

        failure {
            script {
                // Send a failure notification to Slack using the webhook
                sh """
                    curl -X POST -H 'Content-type: application/json' --data '{"text":"Deployment of branch ${params.BRANCH} to ${params.ENVIRONMENT} failed for my-psychometric-exam."}' ${SLACK_WEBHOOK_URL}
                """
            }
        }
    }
}

