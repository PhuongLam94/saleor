node {
    
    withCredentials([string(credentialsId: 'saleor_secret_text', variable: 'SECRET_KEY')]){
        stage('Checkout scm'){
            checkout scm
        }
        withPythonEnv('/usr/local/bin/python3'){
            stage('Install python packages') {
                sh 'python --version'
                sh 'pip install -r requirements.txt'
            }
            stage('DB stuffs') {
                sh 'psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolename=\'saleor\'" | grep -q 1 || psql -c "create role saleor with login password \'saleor\';"'
                sh 'createdb saleor'
                sh 'python manage.py migrate'
            }
            stage('FE stuffs'){
                sh 'npm install'
                sh 'npm run build-assets'
                sh 'npm run build-emails'
            }
            stage ('Deploy'){
                sh 'python manage.py runserver'
            }
        }
        
    }
}