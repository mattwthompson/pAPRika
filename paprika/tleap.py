import os as os
import re as re
import subprocess as sp

import logging as log
import numpy as np
import parmed as pmd
from parmed.structure import Structure as ParmedStructureClass
from paprika import utils

### New Changes:
# Allows building an in vacuo prmtop
# Restores two logic gates in adjust_buffer_value which gives a big speed up in solvation
# Allows option to not write out prmtop, speeds things up cb6-but solv with 2922 by from 10 seconds to 6 seconds
# Allows user to change max_cycles

### Issues: 
# Do we check change in volume often enough?
# The reason we want to remove test files after each test is so they don't pollute other tests 


N_A = 6.0221409 * 10 ** 23
ANGSTROM_CUBED_TO_LITERS = 1 * 10 ** -27

class System(object):
    """ tLEaP build class """

    def __init__(self):

        ### User Settings: Defaults
        self.template_file = None
        self.template_lines = None
        self.loadpdb_file = None
        self.unit = 'model'
        self.pbc_type = 'cubic'
        self.buffer_target = '12.0A'
        self.water_box = 'TIP3PBOX'
        self.neutralize = True
        self.counter_cation='Na+'
        self.counter_anion='Cl-'
        self.add_ions = None
        self.output_path='./'
        self.output_prefix='build'

        ### Other Settings: Defaults
        # The buffer value that is passed to solvatebox or solvateoct
        self.buffer_value = 1.0
        # The target number of waters which we are trying to add
        self.target_waters = 1000
        # Initial self.exponent used to narrow the search of buffer values to give a target number of waters...
        self.exponent = 1
        self.cyc_since_last_exp_change = 0
        # Maximum cycles of adjusting buffer_value for targeting the correct number of waters
        self.max_cycles = 50
        # Waters to remove during the manual removal phase
        self.waters_to_remove = None
        # If self.add_ions, this list will be prepared from processing self.add_ions
        self.add_ion_residues = None
        # List of buffer values attempted...
        self.buffer_val_history = [0]
        # Number of waters corresponding to each buffer value...
        self.wat_added_history = [0]

    def build(self):
        """
        Run appropriate tleap for settings
        """

        # Check input
        if self.template_file and self.template_lines:
            raise Exception('template_file and template_lines cannot both be specified')
        elif self.template_file:
            with open(self.template_file, 'r') as f:
                self.template_lines = f.read().splitlines()
        elif self.template_lines:
            for i,line in enumerate(self.template_lines):
                self.template_lines[i] = line.rstrip()
        else:
            raise Exception('Either template_file or template_lines needs to be specified')

        ### DAVE WOULD LIKE TO SEE THIS BECOME A GENERAL UTILITY!!!
        # Make sure path is low maintenance
        if self.output_path[-1] != '/':
            self.output_path += '/'

        # Filter out any interfering lines
        self.filter_template()

        # Either just write/run tleap, or do solvate
        if self.pbc_type is None:
            self.write_input()
            self.run()
        else:
            self.solvate()

    def filter_template(self):
        """
        Find any lines that may interfere with what we are doing
        """

        filtered_lines = []
        for line in self.template_lines:
            # Find loadpdb line, replace pdb file if necessary, set unit name
            if re.search('loadpdb', line):
                words = line.rstrip().replace('=', ' ').split()
                if self.loadpdb_file is None:
                    self.loadpdb_file = words[2]
                self.unit = words[0]
                filtered_lines.append("{} = loadpdb {}".format(self.unit, self.loadpdb_file))
            # Remove any included solvation and ionization commands if pbc_type is not None
            elif self.pbc_type is not None:
                if not re.search(r"^\s*(addions|addions2|addionsrand|desc|quit|solvate|save)", line, re.IGNORECASE):
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)

        self.template_lines = filtered_lines


    def write_input(self, include_saves=True):
        """
        Write a `tleap` input file using lines from a template.
    
        """

    ##### ADD OPTION TO NOT WRITE OUT PRMTOP/INPCRD FOR QUICK CHECK!!!! #####################

        file_path = self.output_path + self.output_prefix + '.tleap.in'
        with open(file_path, 'w') as f:
            for line in self.template_lines:
                f.write(line+"\n")
    
            if self.pbc_type == 'cubic':
                f.write("solvatebox {} {} {} iso\n".format(self.unit, self.water_box, self.buffer_value))
            elif self.pbc_type == 'rectangular':
                f.write("solvatebox {} {} {{10.0 10.0 {}}}\n".format(self.unit, self.water_box, self.buffer_value))
            elif self.pbc_type == 'octahedral':
                f.write("solvateoct {} {} {} iso\n".format(self.unit, self.water_box, self.buffer_value))
            elif self.pbc_type is None:
                f.write("# Skipping solvation ...\n")
            else:
                raise Exception(
                    "Incorrect pbctype value provided: " + str(self.pbc_type) \
                    + ". Only `cubic`, `rectangular`, `octahedral`, and None are valid")
            if self.neutralize:
                f.write("addionsrand {} {} 0\n".format(self.unit, self.counter_cation))
                f.write("addionsrand {} {} 0\n".format(self.unit, self.counter_anion))
            # Additional ions should be specified as a list, with residue name and number of ions in pairs, like ['NA',
            # 5] for five additional sodium ions. By this point, if the user specified a molality or molarity,
            # it should already have been converted into a number.
            if self.add_ion_residues:
                for residue, amount in zip(self.add_ion_residues[0::2],
                                           self.add_ion_residues[1::2]):
                    f.write("addionsrand {} {} {}\n".format(self.unit, residue, amount))
            if self.waters_to_remove:
                for water_number in self.waters_to_remove:
                    f.write("remove {} {}.{}\n".format(self.unit, self.unit, water_number))
    
            # Note, the execution of tleap is assumed to take place in the
            # same directory as all the associated input files, so we won't
            # put directory paths on the saveamberparm or savepdb commands.
            if self.output_prefix and include_saves:
                f.write("savepdb {} {}.pdb\n".format(self.unit, self.output_prefix))
                f.write("saveamberparm {} {}.prmtop {}.rst7\n".format(self.unit, self.output_prefix,
                                                                      self.output_prefix))
            else:
                pass
            f.write("desc {}\n".format(self.unit))
            f.write("quit\n")

    def run(self):
        """
        Run `tleap`
    
        """
    
        # Consider moving this thing into here.  what does it do?
        utils.check_for_leap_log(path=self.output_path)
        file_name = self.output_prefix + '.tleap.in'    
        p = sp.Popen(['tleap', '-s ', '-f ', file_name], stdout=sp.PIPE, bufsize=1, universal_newlines=True, cwd=self.output_path)
        output = []
        # Wait until process terminates...
        while p.poll() is None:
            line = p.communicate()[0]
            output.append(line)
        if p.poll() is None:
            p.kill()
        self.grep_leap_log()
        return output

    def grep_leap_log(self):
        """
        Check for a few keywords in the `tleap` output.
        """
        try:
            with open(self.output_path + 'leap.log', 'r') as file:
                for line in file.readlines():
                    if re.search('ERROR|WARNING|Warning|duplicate|FATAL|Could', line):
                        log.warning(
                            'It appears there was a problem with solvation: check `leap.log`...'
                        )
        except:
            return


    def solvate(self):
        """
        Solvate a structure with `tleap` to an exact number of waters or buffer size.
    
        """
    
        # If `buffer_target` is a string ending with 'A', an estimate of the number of waters is generated, otherwise,
        # the target is returned.
        self.set_target_waters()
    
        if self.add_ions:
            self.set_additional_ions()
    
        # First, a coarse adjustment...
        # This will run for 50 iterations or until we (a) have more waters than the target and (b) are within ~12 waters
        # of the target (that can be manually removed).
        cycle = 0
        while cycle < self.max_cycles:
            # Start by not manually removing any water, just adjusting the buffer value to get near the target number of
            # waters...

            # Find out how many waters for *this* buffer value...
            waters = self.count_waters()
            self.wat_added_history.append(waters)
            self.buffer_val_history.append(self.buffer_value)
            log.debug("Cycle {:02.0f}   {:8.5f} {:6.0f} ({:6.0f})".format(cycle, self.buffer_value, waters, self.target_waters))
    
            # Possible location of a switch to adjust the buffer_value by polynomial
            # fit approach.
    
            # If we've nailed it, break!
            if waters == self.target_waters:
                # Run one more time and save files
                self.write_input(include_saves=True)
                self.run()
                return
            # If we are close, go to fine adjustment...
            elif waters > self.target_waters and (waters - self.target_waters) < 12:
                self.remove_waters_manually()
                self.write_input(include_saves=True)
                self.run()
                return
            # Otherwise, try to keep adjusting the number of waters...
            else:
                self.adjust_buffer_value()
                # Now that we're close, let's re-evaluate how many ions to add, in case the volume has changed a lot.
                # (This could be slow and run less frequently...)
                ################# HOW DO WE KNOW THAT ONCE EVERY 10 IS GOOD ENOUGH??????????????????????????!!!!!!!!!!!!!!!!!!
                if self.add_ions and cycle % 10 == 0:
                    self.set_additional_ions()
                cycle += 1
    
        if cycle >= self.max_cycles and waters > self.target_waters:
            self.remove_waters_manually()
            self.write_input(include_saves=True)
            self.run()
    
        if cycle >= self.max_cycles and waters < self.target_waters:
            raise Exception("Automatic adjustment of the buffer value resulted in fewer waters \
                added than targeted by `buffer_water`. Try increasing the tolerance in the above loop")
        else:
            raise Exception("Automatic adjustment of the buffer value was unable to converge on \
                a solution with sufficient tolerance")


    def set_target_waters(self):
        """
        Determine the target number of waters by parsing the `buffer_target` option.
    
        Sets
        -------
        self.target_waters : int
            The desired number of waters for the solvation
    
        """
    
        # If buffer_water ends with 'A', meaning it is a buffer distance...
        if isinstance(self.buffer_target, str) and self.buffer_target[-1] == 'A':
            # Let's get a rough value of the number of waters if the buffer target is given as a string.
            # This could fail if there is a space in `buffer_target`...
            self.buffer_value = float(self.buffer_target[:-1])
            waters = self.count_waters()
            log.debug('Initial guess of {} waters for a buffer size of {}...'.format(waters, self.buffer_target))
            # This is now the target number of waters for solvation...
            self.target_waters = waters
        elif isinstance(self.buffer_target, int):
            self.target_waters = self.buffer_target
        # Otherwise, the number of waters to add is specified as an integer, not a distance...
        else:
            raise Exception("The `buffer_target` should either be a string ending with 'A' (e.g., 12A) for 12 Angstroms of "
                            "buffer or an int (e.g., 2000) for 2000 waters.")

    def count_waters(self):
        """
        Quickly check the number of waters added for a given buffer size.
        """
        waters = self.count_residues()['WAT']
        return waters

    def count_residues(self):
        """
        Run and parse `tleap` output and return a dictionary of residues in the structure.
    
        Returns
        -------
        residues : dict
            Dictionary of added residues and their number
        """
        self.write_input(include_saves=False)
        output = self.run()
        # Return a dictionary of {'RES' : number of RES}
        residues = {}
        for line in output[0].splitlines():
            # Is this line a residue from `desc` command?
            match = re.search("^R<(.*) ", line)
            if match:
                residue_name = match.group(1)
                # If this residue is not in the dictionary, initialize and
                # set the count to 1.
                if residue_name not in residues:
                    residues[residue_name] = 1
                # If this residue is in the dictionary, increment the count
                # each time we find an instance.
                elif residue_name in residues:
                    residues[residue_name] += 1
        #log.debug(residues)
        return residues

    def set_additional_ions(self):
        """
        Determine whether additional ions (instead of or in addition to neutralization) are requested...
    
        Sets
        -------
        self.add_ion_residues : list
            A processed list of ions and their amounts that can be passed to `tleap`
    
        """
        if not self.add_ions:
            return None
        if len(self.add_ions) < 2:
            raise Exception("No amount specified for additional ions.")
        if len(self.add_ions) % 2 == 1:
            raise Exception("The 'add_ions' list requires an even number of elements. "
                            "Make sure there is a residue mask followed by a value for "
                            "each ion to be added (or molarity ending in 'M' or molality ending in 'm').")
        self.add_ion_residues = []
        for ion, amount in zip(self.add_ions[0::2], self.add_ions[1::2]):
            self.add_ion_residues.append(ion)
            if isinstance(amount, int):
                self.add_ion_residues.append(amount)
            elif isinstance(amount, str) and amount[-1] == 'm':
                # User specifies molality...
                # number to add = (molality) x (number waters) x (0.018 kg/mol per water)
                number_to_add = int(np.ceil(float(amount[:-1]) * self.target_waters * 0.018))
                self.add_ion_residues.append(number_to_add)
            elif isinstance(amount, str) and amount[-1] == 'M':
                # User specifies molarity...
                volume = self.get_volume()
          ################# raise Exception if volume is None?????????? ########################################!!!!!!!!!!!!
                number_of_atoms = float(amount[:-1]) * N_A
                liters = volume * ANGSTROM_CUBED_TO_LITERS
                number_to_add = int(np.ceil(number_of_atoms * liters))
                self.add_ion_residues.append(number_to_add)
            else:
                raise Exception('Unanticipated error calculating how many ions to add.')

    def get_volume(self):
        """
        Run and parse `tleap` output and return the volume of the structure.
    
        Returns
        -------
        volume : float
            The volume of the structure in cubic angstroms
    
        """
        output = self.run()
        # Return the total simulation volume
        for line in output[0].splitlines():
            line = line.strip()
            if "Volume" in line:
                match = re.search("Volume(.*)", line)
                volume = float(match.group(1)[1:-4])
                return volume
        log.warning('Could not determine total simulation volume.')
        return None

    def remove_waters_manually(self):
        """
        Remove a few water molecules manually with `tleap` to exactly match a desired number of waters.
    
        """
    
        cycle = 0
        max_cycles = 10
        waters = self.wat_added_history[-1]
        while waters > self.target_waters:
            # Retrieve excess water residues
            water_surplus = (waters - self.target_waters)
            water_residues = self.list_waters()
            self.waters_to_remove = water_residues[-1 * water_surplus:]
            log.debug('Manually removing waters... {}'.format(self.waters_to_remove))

            # Get counts for all residues
            residues = self.count_residues()

            # Check if we reached target
            waters = residues['WAT']
            if waters == self.target_waters:
                for key, value in sorted(residues.items()):
                    log.info('{}\t{}'.format(key, value))
                return
            cycle += 1
            if cycle > max_cycles:
                raise Exception(
                    "Solvation failed due to an unanticipated problem with water removal."
                )

    def list_waters(self):
        """
        Run and parse `tleap` output and return the a list of water residues.
    
        Returns
        -------
        water_residues : list
            A list of the water residues in the structure
        """
        output = self.run()
    
        # Return a list of residue numbers for the waters
        water_residues = []
        for line in output[0].splitlines():
            # Is this line a water?
            match = re.search("^R<WAT (.*)>", line)
            if match:
                water_residues.append(match.group(1))
        return water_residues

    def adjust_buffer_value(self):
        """
        Determine whether to increase or decrease the buffer thickness to match a desired number of waters.
    
        Sets
        -------
        self.buffer_value : float
            A new buffer size to try
        self.exponent : int
            Adjusts the order of magnitue of buffer value changes
    
        """
    
        # If the number of waters was less than the target and is now greater than the target, make the buffer a bit
        # smaller, by an increasingly smaller amount, (if we've taken more than one step since the last exponent change)
        if self.wat_added_history[-2] < self.target_waters and self.wat_added_history[-1] > self.target_waters and self.cyc_since_last_exp_change > 1:
            log.debug('Adjustment loop 1')
            self.exponent -= 1
            self.cyc_since_last_exp_change = 0
            self.buffer_value = self.buffer_val_history[-1] + -5 * (10**self.exponent)
        # If the number of waters was greater than the target and is now less than the target, make the buffer a bit
        # bigger, by an increasingly smaller amount, (if we've taken more than one step since the last exponent change)
        elif self.wat_added_history[-2] > self.target_waters and self.wat_added_history[-1] < self.target_waters and self.cyc_since_last_exp_change > 1:
            log.debug('Adjustment loop 2')
            self.exponent -= 1
            self.cyc_since_last_exp_change = 0
            self.buffer_value = self.buffer_val_history[-1] + 5 * (10**self.exponent)
        # If the last two rounds of solvation have too many waters, make the buffer smaller...
        elif self.wat_added_history[-2] > self.target_waters and self.wat_added_history[-1] > self.target_waters:
            log.debug('Adjustment loop 3')
            self.buffer_value = self.buffer_val_history[-1] + -1 * (10**self.exponent)
            self.cyc_since_last_exp_change += 1
        # If the number of waters was greater than the target and is now less than the target, make the buffer a bit
        # bigger ...
        elif self.wat_added_history[-2] > self.target_waters and self.wat_added_history[-1] < self.target_waters:
            log.debug('Adjustment loop 4')
            self.buffer_value = self.buffer_val_history[-1] + 1 * (10**self.exponent)
            self.cyc_since_last_exp_change += 1
        # If the number of waters was less than the target and is now greater than the target, make the buffer a bit
        # smaller ...
        elif self.wat_added_history[-2] < self.target_waters and self.wat_added_history[-1] > self.target_waters:
            log.debug('Adjustment loop 5')
            self.buffer_value = self.buffer_val_history[-1] + -1 * (10**self.exponent)
            self.cyc_since_last_exp_change += 1
        # If the last two rounds of solvation had too few waters, make the buffer bigger...
        elif self.wat_added_history[-2] < self.target_waters and self.wat_added_history[-1] < self.target_waters:
            log.debug('Adjustment loop 6')
            self.buffer_value = self.buffer_val_history[-1] + 1 * (10**self.exponent)
            self.cyc_since_last_exp_change += 1
        else:
            raise Exception(
                "The buffer_values search died due to an unanticipated set of variable values"
            )











