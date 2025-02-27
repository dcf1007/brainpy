import re

from collections import Counter

from .mass_dict import nist_mass

_isotope_string = r'^([A-Z][a-z+]*)(?:\[(\d+)\])?$'
_atom = r'([A-Z][a-z+]*)(?:\[(\d+)\])?([+-]?\d+)?'
_formula = r'^({})*$'.format(_atom)
atom_pattern = re.compile(_atom)
formula_pattern = re.compile(_formula)


def calculate_mass(composition, mass_data=None):
    """Calculates the monoisotopic mass of a composition

    Parameters
    ----------
    composition : Mapping
        Any Mapping type where keys are element symbols and values are integers
    mass_data : dict, optional
        A dict with the masses of the chemical elements (the default
        value is :py:data:`nist_mass`).

    Returns
    -------
        mass : float
    """
    mass = 0.0
    if mass_data is None:
        mass_data = nist_mass
    for element in composition:
        try:
            mass += (composition[element] * mass_data[element][0][0])
        except KeyError:
            match = re.search(r"(\S+)\[(\d+)\]", element)
            if match:
                element_ = match.group(1)
                isotope = int(match.group(2))
                mass += composition[element] * mass_data[element_][isotope][0]
            else:
                raise
    return mass


def _make_isotope_string(element, isotope=0):
    if isotope == 0:
        return element
    else:
        return "%s[%d]" % (element, isotope)


def _get_isotope(element_string):
    if "[" in element_string:
        match = re.search(r"(\S+)\[(\d+)\]", element_string)
        if match:
            element_ = match.group(1)
            isotope = int(match.group(2))
            return element_, isotope
    else:
        return element_string, 0


class PyComposition(Counter):
    '''A mapping representing a chemical composition.

    Implements arithmetic operations, +/- is defined
    between a :class:`PyComposition` and a :class:`Mapping`-like
    object, and * is defined between a :class:`PyComposition` and
    an integer.
    '''
    def __init__(self, base=None, **kwargs):
        if base is not None:
            self.update(base)
        else:
            if kwargs:
                self.update(kwargs)

    def __missing__(self, key):
        return 0

    def __mul__(self, i):
        inst = self.copy()
        for key, value in self.items():
            inst[key] = value * i
        return inst

    def __imul__(self, i):
        for key, value in list(self.items()):
            self[key] = value * i
        return self

    def mass(self, mass_data=None):
        '''Calculate the monoisotopic mass of this chemical composition

        Returns
        -------
        float
        '''
        return calculate_mass(self, mass_data)


def parse_formula(formula):
    """Parse a chemical formula and construct a :class:`PyComposition` object

    Parameters
    ----------
    formula : :class:`str`

    Returns
    -------
    :class:`PyComposition`

    Raises
    ------
    ValueError
        If the formula doesn't match the expected pattern
    """
    if not formula_pattern.match(formula):
        raise ValueError("%r does not look like a formula" % (formula,))
    composition = PyComposition()
    for elem, isotope, number in atom_pattern.findall(formula):
        composition[_make_isotope_string(elem, int(isotope) if isotope else 0)] += int(number) if number else 1
    return composition


try:
    _has_c = True
    _parse_formula = parse_formula
    _PyComposition = PyComposition
    from ._c.composition import parse_formula, PyComposition
except ImportError as e:
    print(e)
    _has_c = False


SimpleComposition = PyComposition
