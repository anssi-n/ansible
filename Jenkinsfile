pipeline {
    agent {
        label 'vagrant && ansible' 
    }
    
    environment {
        LOAD_BALANCER       = 1
        ETCD_NODES          = 3 
        CONTROL_PLANE_NODES = 3 
        WORKER_NODES        = 0 
        VAGRANT_CWD         = 'kubernetes/'
        ANSIBLE_CONFIG      = 'kubernetes/ansible.cfg'
    }

    stages {
        // stage('Checkout') {
        //     steps {
        //         checkout([
        //             $class: 'GitSCM', 
        //             branches: [[name: '*/main']], 
        //             extensions: [], 
        //             userRemoteConfigs: [[url: 'https://github.com/anssi-n/ansible.git']]
        //         ])
        //     }
        // }
        stage('Create target hosts and inventory') {
            steps {
                sh 'kubernetes/generate_inventory.sh kubernetes/inventory.ini'
                sh 'cat kubernetes/inventory.ini'
                sh 'vagrant up'
                sleep 10
            }
        }

        stage('Run ansible playbook') {
            steps {
                ansiblePlaybook(
                    playbook: 'kubernetes/install-k8s.yaml',
                    inventory: 'kubernetes/inventory.ini',
                    tags: 'lb,setup,etcd,init_cluster,join_control',
                    colorized: false,
                    disableHostKeyChecking: true,
                )
            }
        }
        stage('Destroy target hosts') {
            steps {
                sh 'vagrant destroy --force'
            }
        }
    }
    post {
        failure {
            sh 'vagrant destroy --force'
        }
    }
}
