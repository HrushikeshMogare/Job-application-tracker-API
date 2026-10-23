// Planned CI/CD for phase 08. Needs a Jenkins agent with Python 3.12, Docker and Docker Compose.
// GitHub webhook -> Jenkins -> install -> test -> build image -> deploy locally.
pipeline {
    agent any

    environment {
        IMAGE = "job-application-tracker-api"
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build -t ${IMAGE}:${BUILD_NUMBER} -t ${IMAGE}:latest .'
            }
        }

        stage('Deploy (local Docker)') {
            steps {
                sh '''
                    [ -f .env ] || cp .env.example .env
                    docker compose up -d --build
                '''
            }
        }
    }

    post {
        failure { echo 'Pipeline failed. Deployment was skipped or incomplete.' }
    }
}
