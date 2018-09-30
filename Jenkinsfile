node {
    withCredentials([string(credentialsId: 'saleor_secret_text', variable: 'SECRET_KEY')]){
    //if venv folder is not available, create
    if (!fileExist('bin') || !fileExist('lib'))
        stage('Create virtual env') {
            sh 'python3 -m venv saleor-env'
        }
    stage ('Switch to venv'){
        sh 'source /saleor-env/bin/activate'
        sh 'cd ..'
    }
    stage('Install python packages') {
        echo 'pip install -r requirements.txt'
    }
    stage('DB stuffs') {
        sh 'createuser --superuser --pwprompt saleor'
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