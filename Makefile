# This make file was available in: https://gist.githubusercontent.com/zambonin/987cfed2afefb892723ded8252ae5565/raw/e8763581d7fe149d6c317ff2af01ac4a51115c72/Makefile
# Provided by one of the coauthors
#
# A Makefile to reduce the noise of a system to run some benchmarks. It
# performs the following OS-wide actions:
#
#  * disables address space layout randomization (ASLR);
#  * sets dynamic frequency scaling governor to ``performance'';
#  * disables frequency boosting;
#  * disables simultaneous multithreading;
#  * creates a control group (cgroup v2) in $CGROUP_PATH to allow processes to
#    run alone in CPU core 0;
#  * moves all CPUs to other cgroups.
#
# One can then use the newly created cgroup by writing the PID of the desired
# program to $CGROUP_PATH/cgroup.procs.
#
# Based on the script and commentary in https://testbit.eu/2023/cgroup-cpuset.

CGROUP_PATH = /sys/fs/cgroup/shield
LAST_CORE_ID = $(shell lscpu --all --parse=CPU | tail -1)
LOGICAL_CORES = $(shell sort -u /sys/devices/system/cpu/cpu*/topology/thread_siblings_list | cut -d, -f2)
CORES_TO_DISABLE = $(patsubst %,%.smt,$(LOGICAL_CORES))
ALL_CORE_IDS = $(shell seq 0 $(LAST_CORE_ID))
CORES_TO_CHANGE = $(patsubst %,%.cpu,$(ALL_CORE_IDS))
ALL_GROUPS_NOT_THIS = $(shell find /sys/fs/cgroup/ -maxdepth 1 -not -wholename $(CGROUP_PATH)/cpuset.cpus -name cpuset.cpus)
GROUPS_TO_CHANGE = $(patsubst %,%.group,$(ALL_GROUPS_NOT_THIS))

define TEE
	echo "$(1)" | sudo tee $(2) >/dev/null
endef

all: disable-aslr set-governor disable-boost disable-smt create-cgroup

disable-aslr: /proc/sys/kernel/randomize_va_space
	$(call TEE,0,$<)

%.cpu: /sys/devices/system/cpu/cpu%/cpufreq/scaling_governor
	$(call TEE,performance,$<)

set-governor: $(CORES_TO_CHANGE)

disable-boost: /sys/devices/system/cpu/cpufreq/boost
	$(call TEE,0,$<)

%.smt: /sys/devices/system/cpu/cpu%/online
	$(call TEE,0,$<)

disable-smt: $(CORES_TO_DISABLE) set-governor

$(CGROUP_PATH):
	sudo mkdir -p $@

$(CGROUP_PATH)/cgroup.subtree_control: $(CGROUP_PATH)
$(CGROUP_PATH)/cpuset.cpus: $(CGROUP_PATH)
$(CGROUP_PATH)/cpuset.cpus.partition: $(CGROUP_PATH)

enable-controllers: $(CGROUP_PATH)/cgroup.subtree_control
	$(call TEE,+cpu +cpuset,$<)

set-cpus-cgroup: $(CGROUP_PATH)/cpuset.cpus
	$(call TEE,0,$<)

%.group: %
	$(call TEE,1-$(LAST_CORE_ID),$<)

set-cpus-elsewhere: $(GROUPS_TO_CHANGE)

set-cgroup-partition: $(CGROUP_PATH)/cpuset.cpus.partition
	$(call TEE,root,$<)

create-cgroup: enable-controllers set-cpus-cgroup set-cpus-elsewhere \
			   set-cgroup-partition
	@echo -e 'Use the command below inside your scripts or shell.\n'
	@echo 'echo "$$$$" | sudo tee '$(CGROUP_PATH)'/cgroup.procs >/dev/null'

clean: enable-aslr unset-governor enable-boost enable-smt remove-cgroup

enable-aslr: /proc/sys/kernel/randomize_va_space
	$(call TEE,2,$<)

unset-governor: enable-smt
	$(call TEE,powersave,/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor)

enable-boost: /sys/devices/system/cpu/cpufreq/boost
	$(call TEE,1,$<)

enable-smt:
	$(call TEE,1,/sys/devices/system/cpu/cpu*/online)

unset-cgroup-partition: $(CGROUP_PATH)/cpuset.cpus.partition
	$(call TEE,member,$<)

remove-cgroup: $(CGROUP_PATH)
	sudo rmdir $(CGROUP_PATH)
