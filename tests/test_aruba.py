import pytest
import yaml
import re

from hier_config.host import Host
from hier_config.options import options_for


class TestSectionalExitingMultipleSections:
    @pytest.fixture(autouse=True)
    def setUpClass(self, options_aruba):
        self.os = "aruba"
        self.options_aruba = options_aruba


    def test_aaa(self):
        actual_config = """
aaa authentication login console group SOHONET-AUTH local
aaa authentication login https-server group SOHONET-AUTH local
aaa authentication login ssh group SOHONET-AUTH local"""

        intended_config = """
aaa authentication allow-fail-through
aaa authentication login ssh local group SOHONET-AUTH
aaa authentication login console local group SOHONET-AUTH
aaa authentication login https-server local group SOHONET-AUTH"""

        remediation = """aaa authentication allow-fail-through
aaa authentication login ssh local group SOHONET-AUTH
aaa authentication login console local group SOHONET-AUTH
aaa authentication login https-server local group SOHONET-AUTH"""

        host = Host("example1.rtr", self.os, self.options_aruba)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())


    def test_aaa_negation(self):
        actual_config = """
aaa authentication allow-fail-through
aaa authentication login console group SOHONET-AUTH local
aaa authentication login https-server group SOHONET-AUTH local
aaa authentication login ssh group SOHONET-AUTH local"""

        intended_config = """
aaa authentication login console group SOHONET-AUTH local
aaa authentication login https-server group SOHONET-AUTH local
aaa authentication login ssh group SOHONET-AUTH local"""

        remediation = """no aaa authentication allow-fail-through"""

        host = Host("example1.rtr", self.os, self.options_aruba)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_acl_apply(self):
        actual_config = """apply access-list ip OLD-ACL control-plane vrf default"""

        intended_config = """apply access-list ip Sohonet-Mgmt-ACL control-plane vrf default"""

        remediation = """apply access-list ip Sohonet-Mgmt-ACL control-plane vrf default"""

        host = Host("example1.rtr", self.os, self.options_aruba)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

    def test_acl_change(self):
        actual_config = """access-list ip Sohonet-Mgmt-ACL
    10 permit any 10.0.0.0/255.0.0.0 any
    20 permit any 67.224.101.0/255.255.255.192 any
    30 permit any 89.16.225.18 any
    40 permit any 193.203.71.176/255.255.255.248 any
    50 permit any 193.203.71.224/255.255.255.248 any
    60 permit any 193.203.87.176/255.255.255.240 any
    70 permit any 193.203.88.16/255.255.255.240 any
    999 deny any any any"""

        intended_config = """access-list ip Sohonet-Mgmt-ACL
    10 permit any 10.0.0.0/255.0.0.0 any
    20 permit any 67.224.101.0/255.255.255.192 any
    30 permit any 89.16.225.18 any
    40 permit any 193.203.71.176/255.255.255.248 any
    50 permit any 193.203.71.224/255.255.255.248 any
    60 permit any 193.203.87.176/255.255.255.240 any
    70 permit any 11.0.0.0/255.0.0.0 any
    80 permit any 193.203.88.16/255.255.255.240 any
    999 deny any any any"""

        remediation = """access-list ip Sohonet-Mgmt-ACL
  no 70 permit any 193.203.88.16/255.255.255.240 any
  70 permit any 11.0.0.0/255.0.0.0 any
  80 permit any 193.203.88.16/255.255.255.240 any
  exit"""

        host = Host("example1.rtr", self.os, self.options_aruba)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())


    def test_radius_server_change(self):
        actual_config = """radius-server host 10.59.24.15 key ciphertext AQBapWqEtaX8vt3kieQ2H+2+KZSBNBcP4Y0IRzngqkIdIQDyEAAAACjjrBb6j1XPECmBVxMBOs0=
radius-server host 10.59.17.15 key ciphertext AQBapWqEtaX8vt3kieQ2H+2+KZSBNBcP4Y0IRzngqkIdIQDyEAAAACjjrBb6j1XPECmBVxMBOs0="""

        intended_config = """radius-server host 10.59.24.15
radius-server host 10.59.17.15"""

        remediation = """no radius-server host 10.59.24.15
no radius-server host 10.59.17.15
radius-server host 10.59.24.15
radius-server host 10.59.17.15"""

        host = Host("example1.rtr", self.os, self.options_aruba)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())