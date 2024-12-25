cmd_/home/tokuda/tmp/linux-sgx-driver/modules.order := {   echo /home/tokuda/tmp/linux-sgx-driver/isgx.ko; :; } | awk '!x[$$0]++' - > /home/tokuda/tmp/linux-sgx-driver/modules.order
