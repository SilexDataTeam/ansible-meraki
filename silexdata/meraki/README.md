# Ansible Collection - silex.meraki

The silex.meraki project provides a dynamic inventory plugin for Ansible to gather Meraki Networks from the Dashboard API and make them visible in the Ansible Inventory.

# Quick Start Guide

Installation

1. Ansible must be installed ([Install guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html))
```yaml
pip install ansible
```
2. Python Meraki SDK must be installed
```yaml
pip install meraki
```
3. Install the collection
```yaml
ansible-galaxy collection install silex.meraki
```
