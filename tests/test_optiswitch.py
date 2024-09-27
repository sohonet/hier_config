import pytest
import yaml
import re
import os

from hier_config.host import Host
from hier_config.options import options_for


class TestSectionalExitingMultipleSections:
    @pytest.fixture(autouse=True)
    def setUpClass(self, options_optiswitch):
        self.os = "optiswitch"
        self.options_optiswitch = options_optiswitch

    def test_traffic_manager_enable(self):
        actual_config = """
traffic-manager
 tm-port 5
  service-node 1
   rate cir 10g cbs 4M
  tm-enable"""

        intended_config = """
traffic-manager
 tm-port 5
  service-node 1
   rate cir 10g cbs 1M
  tm-enable"""

        remediation = """traffic-manager
  tm-port 5
    service-node 1
      rate cir 10g cbs 1M
    tm-enable"""

        host = Host("example1.rtr", self.os, self.options_optiswitch)
        host.load_running_config(actual_config)
        host.load_generated_config(intended_config)
        print(host.remediation_config())
        assert remediation == str(host.remediation_config())

