import argparse
import numpy as np
from ase.io import read, write

__author__ = "Stefan Bringuier"
__email__ = "stefanbringuier@gmail.com"
__version__ = "0.1"
__description__ = """Finite-difference approximation of velocities from XDATCAR AIMD trajectory. Intent is 
                     to use for autocorrelation and other types of analysis as done in https://doi.org/10.5281/zenodo.10573320.
                  """

# Function to apply periodic boundary conditions to displacements
def apply_pbc(displacement, box_lengths):
    for i in range(3):
        if displacement[i] > box_lengths[i] / 2:
            displacement[i] -= box_lengths[i]
        elif displacement[i] < -box_lengths[i] / 2:
            displacement[i] += box_lengths[i]
    return displacement

# Function to calculate velocities using finite differences
def calculate_velocities(frames, dt=0.001):
    '''
        Use forward/backward difference approximation to calculate velocities.

    - frames: list(ASE.Atoms)
    - dt: float - default time unit is 0.001 picoseconds
    '''
    natoms = len(frames[0])
    box_lengths = frames[0].get_cell().lengths()

    num_frames = len(frames)

    for t in range(num_frames):
        velocities = np.zeros((natoms, 3))
        if t < num_frames - 1:
            # Forward difference for all frames except the last
            positions_curr = frames[t].get_positions()
            positions_next = frames[t + 1].get_positions()
            for i in range(natoms):
                displacement = positions_next[i] - positions_curr[i]
                displacement = apply_pbc(displacement, box_lengths)
                velocities[i, :] = displacement / dt
        else:
            # Backward difference for the last frame
            positions_curr = frames[t].get_positions()
            positions_prev = frames[t - 1].get_positions()
            for i in range(natoms):
                displacement = positions_curr[i] - positions_prev[i]
                displacement = apply_pbc(displacement, box_lengths)
                velocities[i, :] = displacement / dt

        frames[t].set_velocities(velocities)

def write_lammps_dump(frames,output="dump.lammps"):
    """
        Crude LAMMPS dump. Not tested for triclinic boxes.
    """
    # Determine unique mass types and assign type IDs
    mass_types = sorted(set(frames[0].get_masses()))
    mass_to_type = {mass: i + 1 for i, mass in enumerate(mass_types)}

    with open('dump.lammps', 'w') as dump_file:
        for t, atoms in enumerate(frames):
            dump_file.write('ITEM: TIMESTEP\n')
            dump_file.write(f'{t}\n')
            dump_file.write('ITEM: NUMBER OF ATOMS\n')
            dump_file.write(f'{len(atoms)}\n')
            dump_file.write('ITEM: BOX BOUNDS pp pp pp\n')
            cell = atoms.get_cell()
            for i in range(3):
                dump_file.write(f'0.0 {cell[i, i]}\n')
            dump_file.write('ITEM: ATOMS id type x y z vx vy vz\n')

            pos = atoms.get_positions()
            vel = atoms.get_velocities()

            for i, atom in enumerate(atoms):
                atom_type = mass_to_type[atom.mass]
                dump_file.write(f'{i+1} {atom_type} {pos[i][0]} {pos[i][1]} {pos[i][2]} {vel[i][0]} {vel[i][1]} {vel[i][2]}\n')

def main(input,output,timestep=0.001):
    """
    timestep is the time in picoseconds between frames!
    """
    # Read all frames using ASE
    if input.endswith('xml'):
        frames = read(input, format='vasp-xml', index=':')
    else:
        frames = read(input, format='vasp-xdatcar', index=':')

    calculate_velocities(frames, timestep)
 
    if output.startswith('dump') or output.endswith('dump'):
        write_lammps_dump(frames,output=output)
    else:
        write(output,format="extxyz")

if __name__ == "__main__":
    """
    Notes:
        - For vasprun.xml timestep should be POTIM/1000 ps (check your INCAR or vasprun.xml)
        - For XDATCAR timestep should be POTIM*NBLOCK/1000 ps (check your INCAR)
    """
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('input', help='Input file (vasprun.xml or XDATCAR)')
    parser.add_argument('output', help='Output file (e.g., dump.lammps or output.extxyz)')
    parser.add_argument('--timestep', type=float, default=0.001, help='Timestep in picoseconds between frames')

    args = parser.parse_args()
    main(args.input, args.output, args.timestep)
