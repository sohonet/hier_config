import pytest
import yaml
import re
import os

from hier_config.host import Host
from hier_config.options import options_for


class TestSectionalExitingMultipleSections:
    @pytest.fixture(autouse=True)
    def setUpClass(self, options_adva):
        self.os = "adva"
        self.options_adva = options_adva

    def test_access_port_alias(self):
        actual_config = """
network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      admin-state unassigned
      service-type evpl
      alias "TBC"
      port-vlan-id 1-0
      a2n-push-port-vid disabled
      priority-mapping-profile prio_map_profile-1
network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      service-type evpl
      port-vlan-id 1-0
      a2n-push-port-vid disabled
      priority-mapping-profile prio_map_profile-1"""

        intended_config = """
network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      admin-state unassigned
      service-type evpl
      alias "HANDOFF-1"
      port-vlan-id 1-0
      a2n-push-port-vid disabled
      priority-mapping-profile prio_map_profile-1
network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      service-type evpl
      alias "HANDOFF-2"
      port-vlan-id 1-0
      a2n-push-port-vid disabled
      priority-mapping-profile prio_map_profile-1"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      alias "HANDOFF-1"
      back
    configure access-port access-1-1-1-7
      alias "HANDOFF-2"
      back
    back
  back"""
        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_network_port_alias(self):
        actual_config = """
network-element ne-1
  configure nte nte104_e-1-1-1
    configure network-port network-1-1-1-1
      mtu 9638
      auto-diagnostic disabled
      media fiber auto-1000-full
      alias "TBC-1"
    configure network-port network-1-1-1-2
      mtu 9638
      auto-diagnostic disabled
      media fiber auto-1000-full"""

        intended_config = '''
network-element ne-1
  configure nte nte104_e-1-1-1
    configure network-port network-1-1-1-1
      mtu 9638
      auto-diagnostic disabled
      media fiber auto-1000-full
      alias "UPLINK-1"
    configure network-port network-1-1-1-2
      mtu 9638
      auto-diagnostic disabled
      media fiber auto-1000-full
      alias "UPLINK-2"'''

        remediation = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure network-port network-1-1-1-1
      alias "UPLINK-1"
      back
    configure network-port network-1-1-1-2
      alias "UPLINK-2"
      back
    back
  back"""
        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_network_port_defaults(self):
        actual_config = '''
network-element ne-1
  configure nte nte104_e-1-1-1
    configure network-port network-1-1-1-1
      mtu 9638
      auto-diagnostic disabled
      media fiber auto-1000-full
      alias "UPLINK"'''

        intended_config = '''
network-element ne-1
  configure nte nte104_e-1-1-1
    configure network-port network-1-1-1-1
      mtu 9638
      media auto auto-speed-detect
      mdix auto
      alias "UPLINK"'''

        remediation = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure network-port network-1-1-1-1
      auto-diagnostic enabled
      media auto auto-speed-detect
      mdix auto
      back
    back
  back"""
        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_configure_mgmt_tunnel_options(self):
        actual_config = """configure communication
  add mgmttunnel 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based ipv4-only enabled 905 disabled 64000 768000 disabled 10.64.89.10 255.255.255.0
  configure mgmttnl mgmt_tnl-1
    dhcp-client-id-control disabled
    dhcp-class-id-control disabled"""

        intended_config = """configure communication
  add mgmttunnel 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based ipv4-only enabled 905 disabled 64000 768000 disabled 10.64.89.10 255.255.255.0
  configure mgmttnl mgmt_tnl-1
    dhcp-client-id-control enabled
    dhcp-class-id-control enabled"""

        remediation = """configure communication
  configure mgmttnl mgmt_tnl-1
    dhcp-client-id-control enabled
    dhcp-class-id-control enabled
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        host.remediation_config()
        assert remediation == str(host.remediation_config())

    def test_remove_mangement_tunnel_with_options(self):
        # Tags config to ignore management bridge changes
        tags_config = [
            # {
            #     "lineage": [
            #         {"startswith": ["configure communication"]},
            #         {"startswith": ["add mgmttunnel-bridge"]},
            #     ],
            #     "add_tags": "includes",
            # },
            {
                "lineage": [
                    {"startswith": ["configure system"]},
                    {"startswith": ["mgmt-traffic-bridge"]},
                ],
                "add_tags": "excludes",
            },
            {
                "lineage": [
                    {"startswith": ["configure communication"]},
                    {
                        "startswith": [
                            "add mgmttunnel" "configure mgmttnl",
                            "add lpbk-if",
                            # "add mgmttunnel-bridge",
                            "configure src-addr",
                        ],
                    },
                ],
                "add_tags": "excludes",
            },
        ]

        actual_config = """configure communication
  add mgmttunnel 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based ipv4-only enabled 905 disabled 64000 768000 disabled 10.64.89.10 255.255.255.0
  configure mgmttnl mgmt_tnl-1
    dhcp-client-id-control disabled
    dhcp-class-id-control disabled"""

        intended_config = """configure communication
  add mgmttunnel-bridge 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based enabled 905 disabled 256000 768000"""

        remediation = """configure communication
  delete mgmttnl mgmt_tnl-1
  add mgmttunnel-bridge 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based enabled 905 disabled 256000 768000
  back"""
        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_tags(tags_config)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(
            host.remediation_config_filtered_text(
                include_tags={}, exclude_tags={"excludes"}
            )
        )
        assert remediation == str(
            re.sub(
                r"\n\s*\n",
                "\n",
                host.remediation_config_filtered_text(
                    include_tags={}, exclude_tags={"excludes"}
                ),
                re.MULTILINE,
            )
        )

    def test_network_elements_lpbk(self):
        actual_config = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure access-port access-1-1-1-6
      admin-state unassigned
      service-type evpl
      alias "CUST-HANDOFF"
      port-vlan-id 1-0
      a2n-push-port-vid disabled
      priority-mapping-profile prio_map_profile-1
      lpbk
        dst-mac-control enabled
        dst-mac 00:80:ea:00:00:99
        swap-sada sada"""

        intended_config = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure access-port access-1-1-1-6
      admin-state unassigned
      service-type evpl
      alias "CUST-HANDOFF"
      port-vlan-id 1-0
      a2n-push-port-vid disabled
      priority-mapping-profile prio_map_profile-1"""

        remediation = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure access-port access-1-1-1-6
      lpbk
        dst-mac-control disabled
        swap-sada none
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_system_acl(self):
        actual_config = """configure system
  acl-entry acl-1
    configure permit ipv4 10.0.0.0 255.0.0.0
    control enabled
  acl-entry acl-2
    configure permit ipv4 192.168.0.0 255.255.255.0"""

        intended_config = """configure system
  acl-entry acl-1
    configure permit ipv4 10.0.0.0 255.0.0.0
    control enabled"""

        remediation = """configure system
  acl-entry acl-2
    control disabled
    configure permit ipv4 0.0.0.0 255.255.255.255
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_dcn(self):
        actual_config = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure dcn
      admin-state unassigned"""

        intended_config = """network-element ne-1
  configure nte nte104_e-1-1-1"""

        remediation = """network-element ne-1
  configure nte nte104_e-1-1-1
    configure dcn
      admin-state in-service
      speed auto
      alias ""
      mdix auto
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_access_port_admin_status(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      admin-state disabled
      admin-state unassigned
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      admin-state unassigned
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_banner(self):
        actual_config = """configure system
  security-banner " Warning Notice \\n Sohonet Ltd. \\n \\n This system is the property of Sohonet Ltd, and is intended for employees and\\n others authorized by Sohonet Ltd in accordance with its stated policies. \\n \\n Unauthorized access or use of this system may subject you to disciplinary \\n action up to and including termination of employment and to civil and \\n criminal sanctions. \\n\\n This system is monitored. Use of this system constitutes consent to such\\n monitoring and users of this system should not expect privacy in such use\\n\\n"
"""

        intended_config = """configure system
  security-banner "                                Warning Notice                                          \\n                                 Sohonet Ltd.                                           \\n                                                                                     \\n   This system is the property of Sohonet Ltd, and is intended for employees and\\n   others authorized by Sohonet Ltd in accordance with its stated policies.                                                                                                  \\n   \\n   Unauthorized access or use of this system may subject you to disciplinary \\n   action up to and including termination of employment and to civil and \\n   criminal sanctions. \\n\\n   This system is monitored.  Use of this system constitutes consent to such\\n   monitoring and users of this system should not expect privacy in such use\\n\\n"
"""

        remediation = """configure system
  security-banner "                                Warning Notice                                          \\n                                 Sohonet Ltd.                                           \\n                                                                                     \\n   This system is the property of Sohonet Ltd, and is intended for employees and\\n   others authorized by Sohonet Ltd in accordance with its stated policies.                                                                                                  \\n   \\n   Unauthorized access or use of this system may subject you to disciplinary \\n   action up to and including termination of employment and to civil and \\n   criminal sanctions. \\n\\n   This system is monitored.  Use of this system constitutes consent to such\\n   monitoring and users of this system should not expect privacy in such use\\n\\n"
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print("HERE")
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_unset_alias(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      a2n-push-port-vid disabled
      alias "CUST-HANDOFF (OLD)"
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      a2n-push-port-vid disabled
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      alias ""
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print("HERE")
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_flow_circuit_name(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW-00084274" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      configure flow flow-1-1-1-7-1
        circuit-name "SNW0081751"
        ctag push-vid 1517
        vlan-members "0:4095"
        configure a2n-policer a2n_policer-1-1-1-7-1-0
          cir 999872000
          eir 128000
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_flow_vid(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1518 none "0:4095" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      configure flow flow-1-1-1-7-1
        circuit-name "SNW0081751"
        ctag push-vid 1518
        vlan-members "0:4095"
        configure a2n-policer a2n_policer-1-1-1-7-1-0
          cir 999872000
          eir 128000
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_flow_vlan_list(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      configure flow flow-1-1-1-7-1
        circuit-name "SNW0081751"
        ctag push-vid 1517
        vlan-members "0:4095"
        configure a2n-policer a2n_policer-1-1-1-7-1-0
          cir 999872000
          eir 128000
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_flow_shaping_rules(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 999872000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      configure flow flow-1-1-1-7-1
        configure a2n-policer a2n_policer-1-1-1-7-1
          cbs 1024
          ebs 16
          cir 999360000
          eir 128000
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 9999360000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      configure flow flow-1-1-1-7-1
        configure a2n-policer a2n_policer-1-1-1-7-1
          cbs 1536
          ebs 16
          cir 9999360000
          eir 128000
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      configure flow flow-1-1-1-7-1
        circuit-name "SNW0081751"
        ctag push-vid 1517
        vlan-members "0:4095"
        configure a2n-policer a2n_policer-1-1-1-7-1-0
          cir 9999360000
          eir 128000
          back
        back
      configure flow flow-1-1-1-7-1
        configure a2n-policer a2n_policer-1-1-1-7-1
          cbs 1536
          cir 9999360000
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_new_flow(self):
        actual_config = ""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 9999360000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      configure flow flow-1-1-1-7-1
        configure a2n-policer a2n_policer-1-1-1-7-1
          cbs 1536
          ebs 16
          cir 9999360000
          eir 128000
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-7
      add flow flow-1-1-1-7-1 "SNW0081751" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1517 none "0:4095" 9999360000 128000 access-interface access-1-1-1-7 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      configure flow flow-1-1-1-7-1
        configure a2n-policer a2n_policer-1-1-1-7-1
          cbs 1536
          ebs 16
          cir 9999360000
          eir 128000
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_access_port_admin_status(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-4
      a2n-push-port-vid disabled
      add flow flow-1-1-1-4-2 "SNW-00090289" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1003 none "0:4095" 999360000 128000 access-interface access-1-1-1-4 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      alias "CUST-HANDOFF-SNW-00090289"
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-4
      a2n-push-port-vid disabled
      add flow flow-1-1-1-4-2 "SNW-00090289" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1003 none "0:4095" 999360000 128000 access-interface access-1-1-1-4 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      admin-state unassigned
      admin-state in-service
      alias "CUST-HANDOFF-SNW-00090289"
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-4
      admin-state unassigned
      admin-state in-service
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())


    def test_delete_flow(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      a2n-push-port-vid disabled
      add flow flow-1-1-1-3-1 "SNW0081819" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1001 none "0:4095" 999360000 128000 access-interface access-1-1-1-3 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      admin-state unassigned
      admin-state in-service
      alias "CUST-HANDOFF-SNW0081819"
      configure flow flow-1-1-1-3-1
        access-learning-ctrl mac-based
        access-max-forwarding-entries 4096
        configure a2n-policer a2n_policer-1-1-1-3-1-0
          cbs 1024
          cir 999360000
          ebs 16
          eir 128000
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 1024
        network-learning-ctrl mac-based
        network-max-forwarding-entries 4096
      configure n2a-shaper port_n2a_shaper-1-1-1-3-1
        buffersize 1024
    configure access-port access-1-1-1-4
      a2n-push-port-vid disabled
      add flow flow-1-1-1-4-2 "SNW-00090289" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1003 none "0:4095" 999360000 128000 access-interface access-1-1-1-4 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      admin-state unassigned
      admin-state in-service
      alias "CUST-HANDOFF-SNW-00090289"
      configure flow flow-1-1-1-4-2
        access-learning-ctrl mac-based
        access-max-forwarding-entries 4096
        configure a2n-policer a2n_policer-1-1-1-4-2-0
          cbs 1024
          cir 999360000
          ebs 16
          eir 128000
        configure a2n-shaper a2n_shaper-1-1-1-4-2-0
          buffersize 1024
        cpd-filter bpdu use-mac-setting
        cpd-filter efm-oam use-mac-setting
        cpd-filter lacp use-mac-setting
        cpd-filter lacp-marker use-mac-setting
        cpd-filter pause use-mac-setting
        cpd-filter port-authen use-mac-setting
        network-learning-ctrl mac-based
        network-max-forwarding-entries 4096
      configure n2a-shaper port_n2a_shaper-1-1-1-4-1
        buffersize 1024
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      a2n-push-port-vid disabled
      add flow flow-1-1-1-3-1 "SNW0081819" regular-evc enabled disabled disabled disabled 1 disabled push-vid 1001 none "0:4095" 999360000 128000 access-interface access-1-1-1-3 network-interface network-1-1-1-1 flow-based n2a-prio-mapping-profile none a2n-prio-mapping-profile none
      admin-state unassigned
      admin-state in-service
      alias "CUST-HANDOFF-SNW0081819"
      configure flow flow-1-1-1-3-1
        access-learning-ctrl mac-based
        access-max-forwarding-entries 4096
        configure a2n-policer a2n_policer-1-1-1-3-1-0
          cbs 1024
          cir 999360000
          ebs 16
          eir 128000
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 1024
        network-learning-ctrl mac-based
        network-max-forwarding-entries 4096
      configure n2a-shaper port_n2a_shaper-1-1-1-3-1
        buffersize 1024
    configure access-port access-1-1-1-4
      a2n-push-port-vid disabled
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-4
      admin-state unassigned
      delete flow flow-1-1-1-4-2
      admin-state unassigned
      admin-state unassigned
      alias ""
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == os.linesep.join([s for s in str(host.remediation_config()).splitlines() if s.strip()])

    def test_remove_buffer_size(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      configure flow flow-1-1-1-3-1
        access-learning-ctrl mac-based
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 1024
      configure n2a-shaper port_n2a_shaper-1-1-1-3-1
        buffersize 1024
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      configure flow flow-1-1-1-3-1
        access-learning-ctrl mac-based
      configure n2a-shaper port_n2a_shaper-1-1-1-3-1
        buffersize 1024
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      configure flow flow-1-1-1-3-1
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 128
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == os.linesep.join([s for s in str(host.remediation_config()).splitlines() if s.strip()])


    def test_change_buffer_size(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      configure flow flow-1-1-1-3-1
        access-learning-ctrl mac-based
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 1024
      configure n2a-shaper port_n2a_shaper-1-1-1-3-1
        buffersize 1024
"""

        intended_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      configure flow flow-1-1-1-3-1
        access-learning-ctrl mac-based
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 2048
      configure n2a-shaper port_n2a_shaper-1-1-1-3-1
        buffersize 1024
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      configure flow flow-1-1-1-3-1
        configure a2n-shaper a2n_shaper-1-1-1-3-1-0
          buffersize 2048
          back
        back
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == os.linesep.join([s for s in str(host.remediation_config()).splitlines() if s.strip()])

    def test_remove_rfc_test(self):
        actual_config = """network-element ne-1
  configure rfc2544-control rfc2544_control-1-1
    add test-stream rfc2544_test_stream-1-1-1 00:80:ea:00:00:01 disabled disabled
    frame-size-list 64
    test-port access-1-1-1-6
    test-type-list throughput,latency,loss-rate
"""

        intended_config = """network-element ne-1
"""

        remediation = """network-element ne-1
  configure rfc2544-control rfc2544_control-1-1
    delete test-stream rfc2544_test_stream-1-1-1
    test-port access-1-1-1-3
    trial-duration 60
    rate-granularity ten-percent
    frame-size-list none
    test-type-list none
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == os.linesep.join([s for s in str(host.remediation_config()).splitlines() if s.strip()])


    def test_remove_mgmt_tunnel_bridge(self):
        actual_config = """configure communication
  add lpbk-if 1 "lo1" ipv4-only 10.32.22.66 255.255.255.0
  add mgmttunnel-bridge 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based enabled 431 disabled 256000 768000
  add mgmttunnel-bridge 3 "access-1-1-1-3-mgmt-bridge" access-1-1-1-3 ethernet vlan-based enabled 431 disabled 256000 768000
  configure src-addr sys-ip-addr "lo1" "lo1"
  delete mgmttnl mgmt_tnl-1
"""

        intended_config = """configure communication
  add lpbk-if 1 "lo1" ipv4-only 10.32.22.66 255.255.255.0
  add mgmttunnel-bridge 1 "sohonetInband" network-1-1-1-1 ethernet vlan-based enabled 431 disabled 256000 768000
  configure src-addr sys-ip-addr "lo1" "lo1"
  delete mgmttnl mgmt_tnl-1
"""

        remediation = """configure communication
  delete mgmttnl-bridge mgmt_tnl-3
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == os.linesep.join([s for s in str(host.remediation_config()).splitlines() if s.strip()])


    def test_disable_n2a_pop_port_vid(self):
        actual_config = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      n2a-pop-port-vid enabled
      a2n-push-port-vid disabled
"""

        intended_config ="""network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      a2n-push-port-vid disabled
"""

        remediation = """network-element ne-1
  configure nte ntexg108-1-1-1
    configure access-port access-1-1-1-3
      n2a-pop-port-vid disabled
      back
    back
  back"""

        host = Host("example1.rtr", self.os, self.options_adva)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == os.linesep.join([s for s in str(host.remediation_config()).splitlines() if s.strip()])

