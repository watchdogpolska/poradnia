$setup = <<SCRIPT
    export DEBIAN_FRONTEND=noninteractive 
    apt-get update
SCRIPT

$dependencies = <<SCRIPT
    export DEBIAN_FRONTEND=noninteractive 
    apt-get install -y python-dev libjpeg-dev zlib1g-dev
    apt-get install -y python-virtualenv 
    pip install virtualenvwrapper
    #source /usr/local/bin/virtualenvwrapper.sh 
    apt-get install -y libfreetype6* libjpeg8-dev libpng12-dev
    apt-get install -y libxml2-dev libxslt-dev python-dev zlib1g-dev
    sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password root'
    sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password password root'
    apt-get install -y mysql-server-5.5 libmysqlclient-dev
    sed -i "s/\(bind-address\s*=\s*\).\+\?/\10.0.0.0/" /etc/mysql/my.cnf
    stop mysql; start mysql
    echo "CREATE DATABASE poradnia; "| mysql -uroot -proot 
    echo '#!/bin/bash' > /tmp/init.sh
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> /tmp/init.sh
    echo "cd /vagrant/" >> /tmp/init.sh
    echo "mkvirtualenv poradnia" >> /tmp/init.sh
    echo "pip install numpy" >> /tmp/init.sh
    echo "pip install http://downloads.sourceforge.net/project/pyml/PyML-0.7.13.3.tar.gz" >> /tmp/init.sh
    echo "pip install -r requirements/local.txt" >> /tmp/init.sh
    echo "cdvirtualenv" >> /tmp/init.sh
    echo 'echo "export DATABASE_URL=\"mysql://root:root@localhost/poradnia\"">> bin/postactivate' >> /tmp/init.sh
    chmod a+x /tmp/init.sh
    cat /tmp/init.sh
    sudo -H -u vagrant bash -c 'source /tmp/init.sh'     
SCRIPT

Vagrant.configure('2') do |config|

    config.vm.box = 'ubuntu/precise64'

    config.ssh.forward_agent = true
    # Forward the dev server port
    config.vm.network :forwarded_port, host: 8000, guest: 8000
    config.vm.network :forwarded_port, host: 33060, guest: 3306

    config.vm.provision "shell", inline: $setup
    config.vm.provision "shell", inline: $dependencies
end
