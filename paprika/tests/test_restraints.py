"""
Tests the restraints utilities.
"""

import logging
import os

import numpy as np
import parmed as pmd
import pytest

from paprika.restraints.restraints import DAT_restraint, create_window_list
from paprika.restraints.utils import (
    extract_guest_restraints,
    get_bias_potential_type,
    get_restraint_values,
)

logger = logging.getLogger(__name__)


def test_DAT_restraint():
    # Method 1
    logger.info("### Testing restraint 1, Method 1")
    rest1 = DAT_restraint()
    rest1.amber_index = True
    rest1.continuous_apr = False
    rest1.auto_apr = False
    rest1.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest1.mask1 = ":CB6@O,O2,O4,O6,O8,O10"
    rest1.mask2 = ":BUT@C3"
    rest1.attach["target"] = 3.0
    rest1.attach["num_windows"] = 4
    rest1.attach["fc_initial"] = 0.0
    rest1.attach["fc_final"] = 3.0
    rest1.pull["fc"] = rest1.attach["fc_final"]
    rest1.pull["num_windows"] = 4
    rest1.pull["target_initial"] = rest1.attach["target"]
    rest1.pull["target_final"] = 6.0
    rest1.release["target"] = rest1.pull["target_final"]
    rest1.release["num_windows"] = rest1.attach["num_windows"]
    rest1.release["fc_initial"] = rest1.attach["fc_initial"]
    rest1.release["fc_final"] = rest1.attach["fc_final"]
    rest1.initialize()
    assert rest1.index1 == [13, 31, 49, 67, 85, 103]
    assert rest1.index2 == [119]
    assert rest1.index3 is None
    assert rest1.index4 is None
    assert np.allclose(
        rest1.phase["attach"]["force_constants"], np.array([0.0, 1.0, 2.0, 3.0])
    )
    assert np.allclose(rest1.phase["attach"]["targets"], np.array([3.0, 3.0, 3.0, 3.0]))
    assert np.allclose(
        rest1.phase["pull"]["force_constants"], np.array([3.0, 3.0, 3.0, 3.0])
    )
    assert np.allclose(rest1.phase["pull"]["targets"], np.array([3.0, 4.0, 5.0, 6.0]))
    assert np.allclose(
        rest1.phase["release"]["force_constants"], np.array([0.0, 1.0, 2.0, 3.0])
    )
    assert np.allclose(
        rest1.phase["release"]["targets"], np.array([6.0, 6.0, 6.0, 6.0])
    )
    window_list = create_window_list([rest1])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "a003",
        "p000",
        "p001",
        "p002",
        "p003",
        "r000",
        "r001",
        "r002",
        "r003",
    ]

    # Method 1a
    logger.info("### Testing restraint 2, Method 1a")
    rest2 = DAT_restraint()
    rest2.amber_index = True
    rest2.continuous_apr = False
    rest2.auto_apr = False
    rest2.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest2.mask1 = ":CB6@O,O2,O4,O6,O8,O10"
    rest2.mask2 = ":BUT@C3"
    rest2.mask3 = ":BUT@C"
    rest2.attach["target"] = 180.0
    rest2.attach["num_windows"] = 4
    rest2.attach["fc_final"] = 75.0
    rest2.pull["fc"] = rest2.attach["fc_final"]
    rest2.pull["num_windows"] = 4
    rest2.pull["target_final"] = 180.0
    rest2.release["target"] = rest2.pull["target_final"]
    rest2.release["num_windows"] = rest2.attach["num_windows"]
    rest2.release["fc_final"] = rest2.attach["fc_final"]
    rest2.initialize()
    assert rest2.index1 == [13, 31, 49, 67, 85, 103]
    assert rest2.index2 == [119]
    assert rest2.index3 == [109]
    assert rest2.index4 is None
    assert np.allclose(
        rest2.phase["attach"]["force_constants"], np.array([0.0, 25.0, 50.0, 75.0])
    )
    assert np.allclose(
        rest2.phase["attach"]["targets"], np.array([180.0, 180.0, 180.0, 180.0])
    )
    assert np.allclose(
        rest2.phase["pull"]["force_constants"], np.array([75.0, 75.0, 75.0, 75.0])
    )
    assert np.allclose(
        rest2.phase["pull"]["targets"], np.array([0.0, 60.0, 120.0, 180.0])
    )
    assert np.allclose(
        rest2.phase["release"]["force_constants"], np.array([0.0, 25.0, 50.0, 75.0])
    )
    assert np.allclose(
        rest2.phase["release"]["targets"], np.array([180.0, 180.0, 180.0, 180.0])
    )
    window_list = create_window_list([rest2])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "a003",
        "p000",
        "p001",
        "p002",
        "p003",
        "r000",
        "r001",
        "r002",
        "r003",
    ]

    # Method 2 (Note auto_apr = True)
    logger.info("### Testing restraint 3, Method 2")
    rest3 = DAT_restraint()
    rest3.amber_index = True
    rest3.continuous_apr = False
    rest3.auto_apr = True
    rest3.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest3.mask1 = ":CB6@O2"
    rest3.mask2 = ":CB6@O"
    rest3.mask3 = ":BUT@C3"
    rest3.mask4 = ":BUT@C"
    rest3.attach["target"] = 90.0
    rest3.attach["fc_increment"] = 25.0
    rest3.attach["fc_initial"] = 0.0
    rest3.attach["fc_final"] = 75.0
    rest3.pull["target_increment"] = 1.0
    rest3.pull["target_final"] = 93.0
    rest3.release["fc_final"] = 75.0
    rest3.initialize()
    assert rest3.index1 == [31]
    assert rest3.index2 == [13]
    assert rest3.index3 == [119]
    assert rest3.index4 == [109]
    assert np.allclose(
        rest3.phase["attach"]["force_constants"], np.array([0.0, 25.0, 50.0, 75.0])
    )
    assert np.allclose(
        rest3.phase["attach"]["targets"], np.array([90.0, 90.0, 90.0, 90.0])
    )
    assert np.allclose(
        rest3.phase["pull"]["force_constants"], np.array([75.0, 75.0, 75.0, 75.0])
    )
    assert np.allclose(
        rest3.phase["pull"]["targets"], np.array([90.0, 91.0, 92.0, 93.0])
    )
    assert np.allclose(
        rest3.phase["release"]["force_constants"], np.array([0.0, 25.0, 50.0, 75.0])
    )
    assert np.allclose(
        rest3.phase["release"]["targets"], np.array([93.0, 93.0, 93.0, 93.0])
    )
    window_list = create_window_list([rest3])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "a003",
        "p000",
        "p001",
        "p002",
        "p003",
        "r000",
        "r001",
        "r002",
        "r003",
    ]

    # Method 2a
    logger.info("### Testing restraint 4, Method 2a")
    rest4 = DAT_restraint()
    rest4.amber_index = True
    rest4.continuous_apr = False
    rest4.auto_apr = False
    rest4.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest4.mask1 = ":CB6@O2"
    rest4.mask2 = ":CB6@O"
    rest4.mask3 = ":BUT@C3"
    rest4.mask4 = ":BUT@C"
    rest4.attach["target"] = 0.0
    rest4.attach["fc_increment"] = 25.0
    rest4.attach["fc_final"] = 75.0
    rest4.pull["fc"] = 75.0
    rest4.pull["target_increment"] = 1.0
    rest4.pull["target_final"] = 3.0
    rest4.release["target"] = 3.0
    rest4.release["fc_increment"] = 25.0
    rest4.release["fc_final"] = 75.0
    rest4.initialize()
    assert rest4.index1 == [31]
    assert rest4.index2 == [13]
    assert rest4.index3 == [119]
    assert rest4.index4 == [109]
    assert np.allclose(
        rest4.phase["attach"]["force_constants"], np.array([0.0, 25.0, 50.0, 75.0])
    )
    assert np.allclose(rest4.phase["attach"]["targets"], np.array([0.0, 0.0, 0.0, 0.0]))
    assert np.allclose(
        rest4.phase["pull"]["force_constants"], np.array([75.0, 75.0, 75.0, 75.0])
    )
    assert np.allclose(rest4.phase["pull"]["targets"], np.array([0.0, 1.0, 2.0, 3.0]))
    assert np.allclose(
        rest4.phase["release"]["force_constants"], np.array([0.0, 25.0, 50.0, 75.0])
    )
    assert np.allclose(
        rest4.phase["release"]["targets"], np.array([3.0, 3.0, 3.0, 3.0])
    )
    window_list = create_window_list([rest4])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "a003",
        "p000",
        "p001",
        "p002",
        "p003",
        "r000",
        "r001",
        "r002",
        "r003",
    ]

    # Method 3
    logger.info("### Testing restraint 5, Method 3")
    rest5 = DAT_restraint()
    rest5.amber_index = True
    rest5.continuous_apr = False
    rest5.auto_apr = False
    rest5.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest5.mask1 = ":CB6@O,O2,O4,O6,O8,O10"
    rest5.mask2 = ":BUT@C*"
    rest5.attach["target"] = 0.0
    rest5.attach["fraction_list"] = [0.0, 0.2, 0.5, 1.0]
    rest5.attach["fc_final"] = 5.0
    rest5.pull["fc"] = rest5.attach["fc_final"]
    rest5.pull["fraction_list"] = [0.0, 0.5, 1.0]
    rest5.pull["target_final"] = 1.0
    rest5.release["target"] = rest5.pull["target_final"]
    rest5.release["fraction_list"] = [0.0, 0.3, 0.6, 1.0]
    rest5.release["fc_final"] = rest5.attach["fc_final"]
    rest5.initialize()
    assert rest5.index1 == [13, 31, 49, 67, 85, 103]
    assert rest5.index2 == [109, 113, 115, 119]
    assert rest5.index3 is None
    assert rest5.index4 is None
    assert np.allclose(
        rest5.phase["attach"]["force_constants"], np.array([0.0, 1.0, 2.5, 5.0])
    )
    assert np.allclose(rest5.phase["attach"]["targets"], np.array([0.0, 0.0, 0.0, 0.0]))
    assert np.allclose(
        rest5.phase["pull"]["force_constants"], np.array([5.0, 5.0, 5.0])
    )
    assert np.allclose(rest5.phase["pull"]["targets"], np.array([0.0, 0.5, 1.0]))
    assert np.allclose(
        rest5.phase["release"]["force_constants"], np.array([0.0, 1.5, 3.0, 5.0])
    )
    assert np.allclose(
        rest5.phase["release"]["targets"], np.array([1.0, 1.0, 1.0, 1.0])
    )
    window_list = create_window_list([rest5])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "a003",
        "p000",
        "p001",
        "p002",
        "r000",
        "r001",
        "r002",
        "r003",
    ]

    # Method 4
    logger.info("### Testing restraint 6, Method 4")
    rest6 = DAT_restraint()
    rest6.amber_index = True
    rest6.continuous_apr = False
    rest6.auto_apr = False
    rest6.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest6.mask1 = ":CB6@O,O2,O4,O6,O8,O10"
    rest6.mask2 = ":BUT@C*"
    rest6.attach["target"] = 0.0
    rest6.attach["fraction_increment"] = 0.25
    rest6.attach["fc_final"] = 5.0
    rest6.pull["fc"] = rest6.attach["fc_final"]
    rest6.pull["fraction_increment"] = 0.5
    rest6.pull["target_final"] = 1.0
    rest6.release["target"] = rest6.pull["target_final"]
    rest6.release["fraction_increment"] = 0.33
    rest6.release["fc_final"] = rest6.attach["fc_final"]
    rest6.initialize()
    assert rest6.index1 == [13, 31, 49, 67, 85, 103]
    assert rest6.index2 == [109, 113, 115, 119]
    assert rest6.index3 is None
    assert rest6.index4 is None
    assert np.allclose(
        rest6.phase["attach"]["force_constants"], np.array([0.0, 1.25, 2.5, 3.75, 5.0])
    )
    assert np.allclose(
        rest6.phase["attach"]["targets"], np.array([0.0, 0.0, 0.0, 0.0, 0.0])
    )
    assert np.allclose(
        rest6.phase["pull"]["force_constants"], np.array([5.0, 5.0, 5.0])
    )
    assert np.allclose(rest6.phase["pull"]["targets"], np.array([0.0, 0.5, 1.0]))
    ### Note, the 6.6 in the following test is wrong ... needs to get fixed.
    assert np.allclose(
        rest6.phase["release"]["force_constants"], np.array([0.0, 1.65, 3.3, 4.95, 6.6])
    )
    assert np.allclose(
        rest6.phase["release"]["targets"], np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    )
    window_list = create_window_list([rest6])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "a003",
        "a004",
        "p000",
        "p001",
        "p002",
        "r000",
        "r001",
        "r002",
        "r003",
        "r004",
    ]

    # Method 5 (Note continuous_apr = True)
    logger.info("### Testing restraint 7, Method 5")
    rest7 = DAT_restraint()
    rest7.amber_index = True
    rest7.continuous_apr = True
    rest7.auto_apr = False
    rest7.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest7.mask1 = ":1@O,O1,:BUT@H1"
    rest7.mask2 = ":CB6@N"
    rest7.attach["target"] = 0.0
    rest7.attach["fc_list"] = [0.0, 0.5, 1.0, 2.0]
    rest7.pull["fc"] = 2.0
    rest7.pull["target_list"] = [0.0, 0.5, 1.0, 1.5]
    rest7.release["target"] = 1.5
    rest7.release["fc_list"] = [0.0, 0.66, 1.2, 2.0]
    rest7.initialize()
    assert rest7.index1 == [13, 14, 111]
    assert rest7.index2 == [3]
    assert rest7.index3 is None
    assert rest7.index4 is None
    assert np.allclose(
        rest7.phase["attach"]["force_constants"], np.array([0.0, 0.5, 1.0, 2.0])
    )
    assert np.allclose(rest7.phase["attach"]["targets"], np.array([0.0, 0.0, 0.0, 0.0]))
    assert np.allclose(
        rest7.phase["pull"]["force_constants"], np.array([2.0, 2.0, 2.0, 2.0])
    )
    assert np.allclose(rest7.phase["pull"]["targets"], np.array([0.0, 0.5, 1.0, 1.5]))
    assert np.allclose(
        rest7.phase["release"]["force_constants"], np.array([0.0, 0.66, 1.2, 2.0])
    )
    assert np.allclose(
        rest7.phase["release"]["targets"], np.array([1.5, 1.5, 1.5, 1.5])
    )
    window_list = create_window_list([rest7])
    assert window_list == [
        "a000",
        "a001",
        "a002",
        "p000",
        "p001",
        "p002",
        "p003",
        "r001",
        "r002",
        "r003",
    ]

    # Just Attach
    logger.info("### Testing restraint 8, just attach")
    rest8 = DAT_restraint()
    rest8.amber_index = True
    rest8.continuous_apr = False
    rest8.auto_apr = False
    rest8.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest8.mask1 = ":CB6@O"
    rest8.mask2 = ":BUT@C3"
    rest8.attach["target"] = 0.0
    rest8.attach["num_windows"] = 4
    rest8.attach["fc_initial"] = 0.0
    rest8.attach["fc_final"] = 3.0
    rest8.initialize()
    assert rest8.index1 == [13]
    assert rest8.index2 == [119]
    assert rest8.index3 is None
    assert rest8.index4 is None
    assert np.allclose(
        rest8.phase["attach"]["force_constants"], np.array([0.0, 1.0, 2.0, 3.0])
    )
    assert np.allclose(rest8.phase["attach"]["targets"], np.array([0.0, 0.0, 0.0, 0.0]))
    assert rest8.phase["pull"]["force_constants"] is None
    assert rest8.phase["pull"]["targets"] is None
    assert rest8.phase["release"]["force_constants"] is None
    assert rest8.phase["release"]["targets"] is None
    window_list = create_window_list([rest8])
    assert window_list == ["a000", "a001", "a002", "a003"]

    # Just Pull
    logger.info("### Testing restraint 9, just pull")
    rest9 = DAT_restraint()
    rest9.amber_index = True
    rest9.continuous_apr = False
    rest9.auto_apr = False
    rest9.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest9.mask1 = ":CB6@O"
    rest9.mask2 = ":BUT@C3"
    rest9.pull["fc"] = 3.0
    rest9.pull["num_windows"] = 4
    rest9.pull["target_initial"] = 0.0
    rest9.pull["target_final"] = 3.0
    rest9.initialize()
    assert rest9.index1 == [13]
    assert rest9.index2 == [119]
    assert rest9.index3 is None
    assert rest9.index4 is None
    assert rest9.phase["attach"]["force_constants"] is None
    assert rest9.phase["attach"]["targets"] is None
    assert np.allclose(
        rest9.phase["pull"]["force_constants"], np.array([3.0, 3.0, 3.0, 3.0])
    )
    assert np.allclose(rest9.phase["pull"]["targets"], np.array([0.0, 1.0, 2.0, 3.0]))
    assert rest9.phase["release"]["force_constants"] is None
    assert rest9.phase["release"]["targets"] is None
    window_list = create_window_list([rest9])
    assert window_list == ["p000", "p001", "p002", "p003"]

    # Just Release
    logger.info("### Testing restraint 10, just release")
    rest10 = DAT_restraint()
    rest10.amber_index = True
    rest10.continuous_apr = False
    rest10.auto_apr = False
    rest10.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-notcentered.pdb"
    )
    rest10.mask1 = ":CB6@O"
    rest10.mask2 = ":BUT@C3"
    rest10.release["target"] = 0.0
    rest10.release["num_windows"] = 3
    rest10.release["fc_initial"] = 0.0
    rest10.release["fc_final"] = 2.0
    rest10.initialize()
    assert rest10.index1 == [13]
    assert rest10.index2 == [119]
    assert rest10.index3 is None
    assert rest10.index4 is None
    assert rest10.phase["attach"]["force_constants"] is None
    assert rest10.phase["attach"]["targets"] is None
    assert rest10.phase["pull"]["force_constants"] is None
    assert rest10.phase["pull"]["targets"] is None
    assert np.allclose(
        rest10.phase["release"]["force_constants"], np.array([0.0, 1.0, 2.0])
    )
    assert np.allclose(rest10.phase["release"]["targets"], np.array([0.0, 0.0, 0.0]))
    window_list = create_window_list([rest10])
    assert window_list == ["r000", "r001", "r002"]

    # Test inconsistent continuous_apr:
    with pytest.raises(Exception):
        window_list = create_window_list([rest7, rest8])

    # Test inconsistent windows:
    with pytest.raises(Exception):
        window_list = create_window_list([rest1, rest10])


def test_get_restraint_values():
    # Test Harmonic restraint
    attach_fractions = np.linspace(0, 1.0, 25)
    initial_distance = 2.65
    pull_distances = np.linspace(0 + initial_distance, 16.0 + initial_distance, 40)

    restraint = DAT_restraint()
    restraint.continuous_apr = True
    restraint.amber_index = True
    restraint.topology = os.path.join(
        os.path.dirname(__file__), "../data/k-cl/k-cl.pdb"
    )
    restraint.mask1 = "@K+"
    restraint.mask2 = "@Cl-"

    restraint.attach["target"] = initial_distance
    restraint.attach["fraction_list"] = attach_fractions
    restraint.attach["fc_final"] = 10.0

    restraint.pull["fc"] = restraint.attach["fc_final"]
    restraint.pull["target_list"] = pull_distances

    restraint.initialize()

    restraint_values = get_restraint_values(restraint, "attach", 0)
    assert restraint_values["r1"] == 0.0
    assert restraint_values["r2"] == 2.65
    assert restraint_values["r3"] == 2.65
    assert restraint_values["r4"] == 999.0
    assert restraint_values["rk2"] == 0.0
    assert restraint_values["rk3"] == 0.0

    restraint_values = get_restraint_values(restraint, "pull", 0)
    assert restraint_values["r1"] == 0.0
    assert restraint_values["r2"] == 2.65
    assert restraint_values["r3"] == 2.65
    assert restraint_values["r4"] == 999.0
    assert restraint_values["rk2"] == 10.0
    assert restraint_values["rk3"] == 10.0

    # Test custom values
    wall = DAT_restraint()
    wall.auto_apr = False
    wall.amber_index = True
    wall.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    wall.mask1 = "@K+"
    wall.mask2 = "@Cl-"

    wall.attach["fc_initial"] = 1.0
    wall.attach["fc_final"] = 1.0

    wall.custom_restraint_values["rk2"] = 1.0
    wall.custom_restraint_values["rk3"] = 1.0
    wall.custom_restraint_values["r2"] = 0.0
    wall.custom_restraint_values["r3"] = 3.5

    wall.attach["target"] = 3.5
    wall.attach["num_windows"] = len(attach_fractions)

    wall.initialize()

    restraint_values = get_restraint_values(wall, "attach", 0)
    assert restraint_values["r1"] == 0.0
    assert restraint_values["r2"] == 0.0
    assert restraint_values["r3"] == 3.5
    assert restraint_values["r4"] == 999.0
    assert restraint_values["rk2"] == 1.0
    assert restraint_values["rk3"] == 1.0

    wall = DAT_restraint()
    wall.auto_apr = False
    wall.amber_index = True
    wall.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    wall.mask1 = "@K+"
    wall.mask2 = "@Cl-"

    wall.attach["fc_initial"] = 1.0
    wall.attach["fc_final"] = 1.0

    wall.custom_restraint_values["rk2"] = 1.0
    wall.custom_restraint_values["rk3"] = 1.0
    wall.custom_restraint_values["r2"] = 3.5
    wall.custom_restraint_values["r3"] = 0.0

    wall.attach["target"] = 3.5
    wall.attach["num_windows"] = len(attach_fractions)

    wall.initialize()

    restraint_values = get_restraint_values(wall, "attach", 0)
    assert restraint_values["r1"] == 0.0
    assert restraint_values["r2"] == 3.5
    assert restraint_values["r3"] == 0.0
    assert restraint_values["r4"] == 999.0
    assert restraint_values["rk2"] == 1.0
    assert restraint_values["rk3"] == 1.0


def test_get_bias_potential_type():
    # Test Harmonic restraint
    attach_fractions = np.linspace(0, 1.0, 25)
    initial_distance = 2.65
    pull_distances = np.linspace(0 + initial_distance, 16.0 + initial_distance, 40)

    restraint = DAT_restraint()
    restraint.continuous_apr = True
    restraint.amber_index = True
    restraint.topology = os.path.join(
        os.path.dirname(__file__), "../data/k-cl/k-cl.pdb"
    )
    restraint.mask1 = "@K+"
    restraint.mask2 = "@Cl-"

    restraint.attach["target"] = initial_distance
    restraint.attach["fraction_list"] = attach_fractions
    restraint.attach["fc_final"] = 10.0

    restraint.pull["fc"] = restraint.attach["fc_final"]
    restraint.pull["target_list"] = pull_distances

    restraint.initialize()

    assert get_bias_potential_type(restraint, "attach", 0) == "restraint"
    assert get_bias_potential_type(restraint, "pull", 0) == "restraint"

    # Test upper wall restraint (1)
    upper = DAT_restraint()
    upper.auto_apr = False
    upper.amber_index = True
    upper.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    upper.mask1 = "@K+"
    upper.mask2 = "@Cl-"

    upper.attach["fc_initial"] = 1.0
    upper.attach["fc_final"] = 1.0

    upper.custom_restraint_values["rk2"] = 1.0
    upper.custom_restraint_values["rk3"] = 1.0
    upper.custom_restraint_values["r2"] = 0.0
    upper.custom_restraint_values["r3"] = 3.5

    upper.attach["target"] = 3.5
    upper.attach["num_windows"] = len(attach_fractions)

    upper.initialize()

    assert get_bias_potential_type(upper, "attach", 0) == "upper_walls"
    assert get_bias_potential_type(upper, "attach", 1) == "upper_walls"

    # Test upper wall restraint (2)
    upper = DAT_restraint()
    upper.auto_apr = False
    upper.amber_index = True
    upper.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    upper.mask1 = "@K+"
    upper.mask2 = "@Cl-"

    upper.attach["fc_initial"] = 1.0
    upper.attach["fc_final"] = 1.0

    upper.custom_restraint_values["rk2"] = 0.0
    upper.custom_restraint_values["rk3"] = 1.0
    upper.custom_restraint_values["r2"] = 3.5
    upper.custom_restraint_values["r3"] = 3.5

    upper.attach["target"] = 3.5
    upper.attach["num_windows"] = len(attach_fractions)

    upper.initialize()

    assert get_bias_potential_type(upper, "attach", 0) == "upper_walls"
    assert get_bias_potential_type(upper, "attach", 1) == "upper_walls"

    # Test upper wall restraint (3)
    upper = DAT_restraint()
    upper.auto_apr = False
    upper.amber_index = True
    upper.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    upper.mask1 = "@K+"
    upper.mask2 = "@Cl-"

    upper.attach["fc_initial"] = 1.0
    upper.attach["fc_final"] = 1.0

    upper.custom_restraint_values["rk2"] = 0.0
    upper.custom_restraint_values["rk3"] = 1.0
    upper.custom_restraint_values["r2"] = 0.0
    upper.custom_restraint_values["r3"] = 3.5

    upper.attach["target"] = 3.5
    upper.attach["num_windows"] = len(attach_fractions)

    upper.initialize()

    assert get_bias_potential_type(upper, "attach", 0) == "upper_walls"
    assert get_bias_potential_type(upper, "attach", 1) == "upper_walls"

    # Test lower wall restraint (1)
    lower = DAT_restraint()
    lower.auto_apr = False
    lower.amber_index = True
    lower.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    lower.mask1 = "@K+"
    lower.mask2 = "@Cl-"

    lower.attach["fc_initial"] = 1.0
    lower.attach["fc_final"] = 1.0

    lower.custom_restraint_values["rk2"] = 1.0
    lower.custom_restraint_values["rk3"] = 1.0
    lower.custom_restraint_values["r2"] = 3.5
    lower.custom_restraint_values["r3"] = 0.0

    lower.attach["target"] = 3.5
    lower.attach["num_windows"] = len(attach_fractions)

    lower.initialize()

    assert get_bias_potential_type(lower, "attach", 0) == "lower_walls"
    assert get_bias_potential_type(lower, "attach", 1) == "lower_walls"

    # Test lower wall restraint (2)
    lower = DAT_restraint()
    lower.auto_apr = False
    lower.amber_index = True
    lower.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    lower.mask1 = "@K+"
    lower.mask2 = "@Cl-"

    lower.attach["fc_initial"] = 1.0
    lower.attach["fc_final"] = 1.0

    lower.custom_restraint_values["rk2"] = 1.0
    lower.custom_restraint_values["rk3"] = 0.0
    lower.custom_restraint_values["r2"] = 3.5
    lower.custom_restraint_values["r3"] = 3.5

    lower.attach["target"] = 3.5
    lower.attach["num_windows"] = len(attach_fractions)

    lower.initialize()

    assert get_bias_potential_type(lower, "attach", 0) == "lower_walls"
    assert get_bias_potential_type(lower, "attach", 1) == "lower_walls"

    # Test lower wall restraint (3)
    lower = DAT_restraint()
    lower.auto_apr = False
    lower.amber_index = True
    lower.topology = os.path.join(os.path.dirname(__file__), "../data/k-cl/k-cl.pdb")
    lower.mask1 = "@K+"
    lower.mask2 = "@Cl-"

    lower.attach["fc_initial"] = 1.0
    lower.attach["fc_final"] = 1.0

    lower.custom_restraint_values["rk2"] = 1.0
    lower.custom_restraint_values["rk3"] = 0.0
    lower.custom_restraint_values["r2"] = 3.5
    lower.custom_restraint_values["r3"] = 6.5

    lower.attach["target"] = 3.5
    lower.attach["num_windows"] = len(attach_fractions)

    lower.initialize()

    assert get_bias_potential_type(lower, "attach", 0) == "lower_walls"
    assert get_bias_potential_type(lower, "attach", 1) == "lower_walls"


def test_extract_guest_restraints():
    """Test extract_guest_restraints to make sure it is extracting the correct restraints."""
    restraints = []

    # Guest - r
    r = DAT_restraint()
    r.amber_index = True
    r.continuous_apr = True
    r.auto_apr = True
    r.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"
    )
    r.mask1 = ":DM1"
    r.mask2 = ":BUT@C3"
    r.attach["target"] = 6.0
    r.attach["num_windows"] = 4
    r.attach["fc_initial"] = 0.0
    r.attach["fc_final"] = 5.0
    r.pull["fc"] = r.attach["fc_final"]
    r.pull["num_windows"] = 46
    r.pull["target_initial"] = r.attach["target"]
    r.pull["target_final"] = 24.0
    r.release["target"] = r.pull["target_final"]
    r.release["num_windows"] = r.attach["num_windows"]
    r.release["fc_initial"] = r.attach["fc_initial"]
    r.release["fc_final"] = r.attach["fc_final"]
    r.initialize()
    restraints.append(r)

    # Guest - theta
    r = DAT_restraint()
    r.amber_index = True
    r.continuous_apr = True
    r.auto_apr = True
    r.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"
    )
    r.mask1 = ":DM1"
    r.mask2 = ":BUT@C3"
    r.mask3 = ":BUT@C"
    r.attach["target"] = 180.0
    r.attach["num_windows"] = 15
    r.attach["fc_initial"] = 0.0
    r.attach["fc_final"] = 100.0
    r.pull["fc"] = r.attach["fc_final"]
    r.pull["num_windows"] = 46
    r.pull["target_initial"] = r.attach["target"]
    r.pull["target_final"] = 180.0
    r.release["target"] = r.pull["target_final"]
    r.release["num_windows"] = r.attach["num_windows"]
    r.release["fc_initial"] = r.attach["fc_initial"]
    r.release["fc_final"] = r.attach["fc_final"]
    r.initialize()
    restraints.append(r)

    # Guest - beta
    r = DAT_restraint()
    r.amber_index = True
    r.continuous_apr = True
    r.auto_apr = True
    r.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"
    )
    r.mask1 = ":DM2"
    r.mask2 = ":DM1"
    r.mask3 = ":BUT@C3"
    r.attach["target"] = 180.0
    r.attach["num_windows"] = 15
    r.attach["fc_initial"] = 0.0
    r.attach["fc_final"] = 100.0
    r.pull["fc"] = r.attach["fc_final"]
    r.pull["num_windows"] = 46
    r.pull["target_initial"] = r.attach["target"]
    r.pull["target_final"] = 180.0
    r.release["target"] = r.pull["target_final"]
    r.release["num_windows"] = r.attach["num_windows"]
    r.release["fc_initial"] = r.attach["fc_initial"]
    r.release["fc_final"] = r.attach["fc_final"]
    r.initialize()
    restraints.append(r)

    structure = pmd.load_file(
        os.path.join(os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"),
        structure=True,
    )
    guest_restraints = extract_guest_restraints(structure, restraints, "BUT")

    assert guest_restraints[0] is not None
    assert guest_restraints[1] is not None
    assert guest_restraints[2] is None
    assert guest_restraints[3] is None
    assert guest_restraints[4] is not None
    assert guest_restraints[5] is None

    # Guest - phi
    r = DAT_restraint()
    r.amber_index = True
    r.continuous_apr = True
    r.auto_apr = True
    r.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"
    )
    r.mask1 = ":DM3"
    r.mask2 = ":DM2"
    r.mask3 = ":DM1"
    r.mask4 = ":BUT@C3"
    r.attach["target"] = 120.0
    r.attach["num_windows"] = 15
    r.attach["fc_initial"] = 0.0
    r.attach["fc_final"] = 100.0
    r.pull["fc"] = r.attach["fc_final"]
    r.pull["num_windows"] = 46
    r.pull["target_initial"] = r.attach["target"]
    r.pull["target_final"] = 120.0
    r.release["target"] = r.pull["target_final"]
    r.release["num_windows"] = r.attach["num_windows"]
    r.release["fc_initial"] = r.attach["fc_initial"]
    r.release["fc_final"] = r.attach["fc_final"]
    r.initialize()
    restraints.append(r)

    guest_restraints = extract_guest_restraints(structure, restraints, "BUT")

    assert guest_restraints[0] is not None
    assert guest_restraints[1] is not None
    assert guest_restraints[2] is not None
    assert guest_restraints[3] is None
    assert guest_restraints[4] is not None
    assert guest_restraints[5] is None

    # Guest - alpha
    r = DAT_restraint()
    r.amber_index = True
    r.continuous_apr = True
    r.auto_apr = True
    r.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"
    )
    r.mask1 = ":DM2"
    r.mask2 = ":DM1"
    r.mask3 = ":BUT@C3"
    r.mask4 = ":BUT@C"
    r.attach["target"] = 50.0
    r.attach["num_windows"] = 15
    r.attach["fc_initial"] = 0.0
    r.attach["fc_final"] = 100.0
    r.pull["fc"] = r.attach["fc_final"]
    r.pull["num_windows"] = 46
    r.pull["target_initial"] = r.attach["target"]
    r.pull["target_final"] = 50.0
    r.release["target"] = r.pull["target_final"]
    r.release["num_windows"] = r.attach["num_windows"]
    r.release["fc_initial"] = r.attach["fc_initial"]
    r.release["fc_final"] = r.attach["fc_final"]
    r.initialize()
    restraints.append(r)

    guest_restraints = extract_guest_restraints(structure, restraints, "BUT")

    assert guest_restraints[0] is not None
    assert guest_restraints[1] is not None
    assert guest_restraints[2] is not None
    assert guest_restraints[3] is not None
    assert guest_restraints[4] is not None
    assert guest_restraints[5] is None

    # Guest - gamma
    r = DAT_restraint()
    r.amber_index = True
    r.continuous_apr = True
    r.auto_apr = True
    r.topology = os.path.join(
        os.path.dirname(__file__), "../data/cb6-but/cb6-but-dum.pdb"
    )
    r.mask1 = ":DM1"
    r.mask2 = ":BUT@C3"
    r.mask3 = ":BUT@C"
    r.mask4 = ":BUT@C2"
    r.attach["target"] = 50.0
    r.attach["num_windows"] = 15
    r.attach["fc_initial"] = 0.0
    r.attach["fc_final"] = 100.0
    r.pull["fc"] = r.attach["fc_final"]
    r.pull["num_windows"] = 46
    r.pull["target_initial"] = r.attach["target"]
    r.pull["target_final"] = 50.0
    r.release["target"] = r.pull["target_final"]
    r.release["num_windows"] = r.attach["num_windows"]
    r.release["fc_initial"] = r.attach["fc_initial"]
    r.release["fc_final"] = r.attach["fc_final"]
    r.initialize()
    restraints.append(r)

    guest_restraints = extract_guest_restraints(structure, restraints, "BUT")

    assert guest_restraints[0] is not None
    assert guest_restraints[1] is not None
    assert guest_restraints[2] is not None
    assert guest_restraints[3] is not None
    assert guest_restraints[4] is not None
    assert guest_restraints[5] is not None
