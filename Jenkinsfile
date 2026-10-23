
pipeline {
    agent any

    environment {
        IMAGE = 'job-application-tracker-api'
        DOCKER = 'C:\\Users\\HP\\AppData\\Local\\Programs\\Docker\\Docker\\resources\\bin\\docker.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install dependencies') {
            steps {
                bat '''
                if not exist .venv\\Scripts\\python.exe python -m venv .venv
                .venv\\Scripts\\python.exe -m pip install --upgrade pip
                .venv\\Scripts\\python.exe -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                bat '.venv\\Scripts\\python.exe -m pytest'
            }
        }

        stage('Check Docker') {
            steps {
                bat '''
                "%DOCKER%" --version
                "%DOCKER%" info
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                bat '''
                "%DOCKER%" build -t %IMAGE%:%BUILD_NUMBER% -t %IMAGE%:latest .
                '''
            }
        }

        stage('Deploy (local Docker)') {
            steps {
                bat '''
                if not exist .env (
                    if exist .env.example (
                        copy .env.example .env
                    ) else (
                        echo No .env.example found; skipping environment file copy.
                    )
                )

                "%DOCKER%" compose up -d --build
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the first failing stage in the console output.'
        }
    }
}
