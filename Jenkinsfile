
pipeline {
    agent any

    environment {
        IMAGE = 'job-application-tracker-api'
        DOCKER = 'C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        DOCKER_CONFIG = 'C:\\Users\\HP\\.docker'
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

        stage('Check Docker Compose') {
            steps {
                bat '''
                echo Checking Docker Compose plugin...
                "%DOCKER%" compose version
                if errorlevel 1 exit /b 1
                "%DOCKER%" compose ls
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
                        echo ERROR: .env.example was not found.
                        exit /b 1
                    )
                )

                "%DOCKER%" compose up -d --build
                if errorlevel 1 exit /b 1

                "%DOCKER%" compose ps
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Check the first failing stage in Console Output.'
        }
    }
}
