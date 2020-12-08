pipeline {
    stages {
        stage('Clean Previous Deployment') {
            steps {
                sh """
                make clean
                """
           }
        }
        stage('Run linter') {
            steps {
                sh """
                ./test.bash
                """
            }
        }
    }
}

