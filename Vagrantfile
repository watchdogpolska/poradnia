# -*- mode: ruby -*-
# vi: set ft=ruby :
Vagrant.configure("2") do |config|
    config.vm.box = 'bento/ubuntu-16.04'

    config.ssh.forward_agent = true
    # Forward the dev server port
    config.vm.network :forwarded_port, host: 8000, guest: 8000
    config.vm.network :forwarded_port, host: 33060, guest: 3306
    config.vm.provision :ansible do |ansible|
        ansible.playbook = "vagrant_provision_ansible.yaml"
    end
end
