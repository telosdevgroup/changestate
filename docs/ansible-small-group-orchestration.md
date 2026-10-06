# Ansible Fleet Orchestration Guide for ChangeState

Managing CPU cores, clock ceilings, and power budgets across a fleet of bare-metal Linux servers, workstation labs, or edge nodes usually involves BIOS changes, vendor IPMI scripts, or brittle ad-hoc sysfs loops. 

`changestate` provides a single, deterministic binary that dynamically auto-discovers each node's hardware and maps overall capacity to standardized prime tiers (`P:2` through `P:31`). This guide shows how to deploy ChangeState across an entire fleet and orchestrate capacity on demand using Ansible.

---

## 1. Prerequisites

- Ansible control node running on your machine or orchestration server.
- Managed nodes running Linux (Debian, Ubuntu, Fedora, Arch, CentOS/RHEL).
- SSH access with `become` (root/sudo) privileges.

---

## 2. Deploying ChangeState to Your Fleet

The deploy playbook installs prerequisites (`python3`, `git`), clones the engine, sets up `/usr/local/bin/changestate`, configures a secure non-interactive sudoers rule, and sets an initial baseline capacity.

A ready-to-run playbook is provided at [`docs/recipes/ansible/changestate-deploy.yml`](recipes/ansible/changestate-deploy.yml):

```yaml
---
- name: Deploy ChangeState to Linux Nodes
  hosts: compute_nodes
  become: true
  vars:
    changestate_repo: "https://github.com/telosdevgroup/changestate.git"
    changestate_version: "main"
    install_dir: "/opt/changestate"
    bin_target: "/usr/local/bin/changestate"
    default_tier: "p11"

  tasks:
    - name: Ensure prerequisite packages are installed
      ansible.builtin.package:
        name:
          - python3
          - git
        state: present

    - name: Clone ChangeState repository
      ansible.builtin.git:
        repo: "{{ changestate_repo }}"
        dest: "{{ install_dir }}"
        version: "{{ changestate_version }}"
        force: true

    - name: Symlink changestate binary to PATH
      ansible.builtin.file:
        src: "{{ install_dir }}/changestate"
        dest: "{{ bin_target }}"
        state: link
        mode: "0755"
        force: true

    - name: Install sudoers rule for non-interactive execution
      ansible.builtin.copy:
        dest: /etc/sudoers.d/changestate
        content: |
          %sudo ALL=(ALL) NOPASSWD: /usr/local/bin/changestate
          %wheel ALL=(ALL) NOPASSWD: /usr/local/bin/changestate
        owner: root
        group: root
        mode: "0440"
        validate: "visudo -cf %s"

    - name: Apply default baseline capacity tier
      ansible.builtin.command: "{{ bin_target }} {{ default_tier }}"
```

### Running the Deployment

```bash
ansible-playbook -i inventory.ini docs/recipes/ansible/changestate-deploy.yml
```

---

## 3. Shifting Capacity Tiers Across Fleets

Once deployed, you can adjust capacity tiers across host groups instantly.

### Method A: Using the Reusable Playbook
Run [`docs/recipes/ansible/changestate-tier-switch.yml`](recipes/ansible/changestate-tier-switch.yml) with the `target_tier` extra-var:

```bash
# Shift all build workers to high-throughput compute (P:29)
ansible-playbook -i inventory.ini docs/recipes/ansible/changestate-tier-switch.yml \
  -l build_workers \
  -e "target_tier=p29"

# Drop lab nodes to whisper-quiet idle (P:7)
ansible-playbook -i inventory.ini docs/recipes/ansible/changestate-tier-switch.yml \
  -l lab_nodes \
  -e "target_tier=p7"
```

### Method B: Ad-Hoc Ansible CLI Commands
For instant manual intervention across a host group:

```bash
# Shift GPU inference hosts to balanced sweet spot (P:23)
ansible gpu_nodes -i inventory.ini -m command -a "changestate p23" --become

# Check active status across all servers
ansible compute_nodes -i inventory.ini -m command -a "changestate status"
```

---

## 4. Querying Fleet Telemetry & Capacity JSON

ChangeState supports machine-readable output out of the box. You can aggregate node hardware stats and active levels into centralized logs or monitoring systems:

```bash
# Fetch discovered topology and tier metadata formatted as JSON from all nodes
ansible compute_nodes -i inventory.ini -m command -a "changestate tiers-json"
```

Each node responds with its detected CPU core count, thread topology, and exact frequency ceilings for each prime tier, making it easy to feed into Prometheus node_exporter or centralized dashboards.
