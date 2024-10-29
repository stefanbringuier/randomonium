from ase import Atoms
from ase.neighborlist import NeighborList, natural_cutoffs
from ase.build import bulk
import numpy as np


class NiTiSystem(Atoms):
    # Default parameters for the order parameter calculation
    default_params = {
        "d0B19": 2.53,  # Angstrom
        "d1B19": 2.87,
        "d0B2": 2.69,
        "d1B2": 2.69,
    }

    @classmethod
    def from_structure(
        cls,
        structure: str = "B2",
        a: float = 3.107,
        params: dict = None,
        skin: float = 1.1,
        **kwargs,
    ) -> "NiTiSystem":
        """
        Create NiTiSystem instances.

        Args:
            structure: str or ASE Atoms, type of structure ('B2', 'B19', 'B19'')
            or existing Atoms object
            a: float, lattice parameter 'a' for B2, or relevant parameter
            for other structures
            params: dict, optional parameters to overwrite default values
            skin: float, optional neighbor list skin, default is 1.1
            **kwargs: additional keyword arguments passed to ASE
            Atoms constructor

        Returns:
            NiTiSystem: new NiTiSystem instance
        """
        # Determine if structure is an Atoms object or a string identifier
        if isinstance(structure, Atoms):
            atoms = structure
        elif structure == "B2":
            atoms = bulk("NiTi", "cesiumchloride", a=a)
        elif structure == "B19":
            raise NotImplementedError("B19 not yet implemented.")
        elif structure == "B19'":
            raise NotImplementedError("B19' not yet implemented.")
        else:
            raise ValueError(f"Unknown structure type '{structure}'")

        # Initialize the NiTiSystem object by copying the atoms data
        obj = cls(
            symbols=atoms.get_chemical_symbols(),
            positions=atoms.get_positions(),
            cell=atoms.get_cell(),
            pbc=True,
            **kwargs,
        )

        # Set custom attributes
        obj.params = {**cls.default_params, **(params or {})}
        obj.skin = skin
        return obj

    def get_order_parameter(self, params=None, skin=None):
        """
        Interface method to get the order parameter.
        """
        if params is not None:
            self.params = {**self.default_params, **params}
        if skin is not None:
            self.skin = skin
        self._calculate_order_parameter()
        return self.get_array("op")

    def _calculate_order_parameter(self):
        """
        Instance method to calculate the order parameter using
        instance-specific parameters.
        """
        op = self.calculate_order_parameter(self, self.params, self.skin)
        self.set_array("op", op)

    @staticmethod
    def calculate_order_parameter(atoms, params, skin=1.1):
        """
        Static method to calculate the order parameter for a given Atoms object.
        """
        if not all(symbol in atoms.get_chemical_symbols() for symbol in ["Ni", "Ti"]):
            print("Skipping order parameter calculation: Not a NiTi system.")
            return None

        natoms = len(atoms)
        orderp = np.zeros(natoms)
        cutoffs = natural_cutoffs(atoms, mult=skin)
        nl = NeighborList(cutoffs, bothways=True, self_interaction=False)
        nl.update(atoms)

        d0B19 = params["d0B19"]
        d1B19 = params["d1B19"]
        d0B2 = params["d0B2"]
        d1B2 = params["d1B2"]

        for i in range(natoms):
            indices, offsets = nl.get_neighbors(i)
            itype = atoms[i].symbol
            distances = []

            for j, offset in zip(indices, offsets):
                jtype = atoms[j].symbol
                if itype == jtype:
                    continue
                rij = (
                    atoms.positions[j]
                    + np.dot(offset, atoms.get_cell())
                    - atoms.positions[i]
                )
                distances.append(np.linalg.norm(rij))

            if len(distances) < 8:
                raise ValueError(
                    f"Atom {i} has fewer than 8 neighbors. Check cutoff radius or structure."
                )

            distances.sort()
            d0 = sum(distances[:6]) / 6.0
            d1 = sum(distances[6:8]) / 2.0
            chi = (d0 * (d1B2 + d1B19) - d1 * (d0B2 + d0B19)) / (d0B2 * (d0B19 - d1B19))
            orderp[i] = chi

        return orderp

    def write(self, filename, format="extxyz", **kwargs):
        """
        Override the ASE Atoms write method to ensure the order parameter
        array is written in the output.

        Use extxyz by default.
        """
        if "op" not in self.arrays:
            print("Order parameter array not found. Calculating before writing.")
            self._calculate_order_parameter()
        super().write(filename, format=format, **kwargs)


if __name__ == "__main__":
    # B2 structure: NiTi with cubic structure
    b2_atoms = NiTiSystem.from_structure(structure="B2")
    b2_order_param = b2_atoms.get_order_parameter()
    print("B2 order parameter:", b2_order_param)
    expected_b2_value = -1.0
    assert np.allclose(
        b2_order_param, expected_b2_value, atol=0.01
    ), "B2 structure test failed."
    b2_atoms.write("b2.extxyz")
    # B19/B19' structures
