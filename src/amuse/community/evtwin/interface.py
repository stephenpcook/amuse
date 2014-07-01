import os.path
from amuse.community import *
from amuse.community.interface.se import StellarEvolution, StellarEvolutionInterface, \
    InternalStellarStructure, InternalStellarStructureInterface

from amuse.support.interface import InCodeComponentImplementation
from amuse.support.options import OptionalAttributes, option


class EVtwinInterface(CodeInterface, LiteratureReferencesMixIn, StellarEvolutionInterface, 
        InternalStellarStructureInterface, 
        CodeWithDataDirectories):
    """
    Evtwin is based on Peter Eggleton's stellar evolution code, and solves 
    the differential equations that apply to the interior of a star. Therefore 
    it is more accurate, but also much slower than the analytic fits-based 
    SSE legacy code, that has the same origin.
    The work-around for the helium flash is not yet implemented in the AMUSE 
    interface to evtwin. Currently only solar metallicity.
    
        .. [#] ** Eggleton, P.P. 1971, MNRAS, 151, 351: "The evolution of low mass stars"
        .. [#] ** Glebbeek, Pols & Hurley, 2008 A&A (for enhancements to the solver)
        .. [#] Eggleton, P.P. 1972, MNRAS, 156, 361: "Composition changes during stellar evolution"
        .. [#] Eggleton, P.P. 1973, MNRAS, 163, 279: "A numerical treatment of double shell source stars"
        .. [#] Eggleton, P.P., Faulkner, J., & Flannery, B.P. 1973, A&A, 23, 325:
        .. [#] ... "An Approximate Equation of State for Stellar Material"
        .. [#] Han, Z., Podsiadlowski, P., & Eggleton, P.P. 1994, MNRAS, 270, 121:
        .. [#] ... "A Possible Criterion for Envelope Ejection in Asymptotic Giant Branch or First Giant Branch Stars"
        .. [#] Pols, O.R., Tout, C.A., Eggleton, P.P., & Han, Z. 1995, MNRAS, 274, 964:
        .. [#] ... "Approximate input physics for stellar modelling"
        .. [#] Eggleton, P.P. 2001, Evolution of Binary and Multiple Star Systems, 229, 157: "The Braking of Wind"
        .. [#] Nelson, C.A., & Eggleton, P.P. 2001, ApJ, 552, 664:
        .. [#] ... "A Complete Survey of Case A Binary Evolution with Comparison to Observed Algol-type Systems"
        .. [#] Eggleton, P.P., & Kiseleva-Eggleton, L. 2002, ApJ, 575, 461: "The Evolution of Cool Algols"
        .. [#] Stancliffe, Glebbeek, Izzard & Pols, 2007 A&A (for thermohaline mixing)
        .. [#] Eldridge & Tout, 2004 MNRAS 348 (for the OPAL 1996 opacity tables)
    """
    use_modules = ['twinlib']
    
    def __init__(self, **options):
        CodeInterface.__init__(self, name_of_the_worker="evtwin_worker", **options)
        LiteratureReferencesMixIn.__init__(self)
        CodeWithDataDirectories.__init__(self)
    
    set_mass_fraction_of_species_at_zone = None
    set_radius_at_zone = None
    set_density_at_zone = None
    set_temperature_at_zone = None
    
    @property
    def default_path_to_ev_database(self):
        return self.get_code_src_directory()
    
    @legacy_function
    def new_zams_star():
        """
        Define a new star in the code: a zero-age main sequence star with the given mass.
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.OUT)
        function.addParameter('mass', dtype='float64', unit=units.MSun, direction=function.IN)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def new_prems_star():
        """
        Define a new star in the code: a pre-main-sequence star with the given mass.
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.OUT)
        function.addParameter('mass', dtype='float64', unit=units.MSun, direction=function.IN)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def new_star_from_file():
        """
        Define a new star in the code: read the model from file.
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.OUT)
        function.addParameter('filename', dtype='string', direction=function.IN)
        function.result_type = 'int32'
        return function
    
    def new_particle_method(self, mass=0|units.MSun, pms=False, filename=None):
        if not filename is None:
            return self.new_star_from_file(filename)
        if pms:
            return self.new_prems_star(mass)
        else:
            return self.new_zams_star(mass)
    new_particle = None
    
    @legacy_function
    def get_maximum_number_of_stars():
        """
        Retrieve the maximum number of stars that can be
        handled by this instance.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('maximum_number_of_stars', dtype='int32', direction=function.OUT,
            description = "The current value of the maximum number of stars")
        function.result_type = 'int32'
        function.result_doc = """
        0 - OK
            Current value of was retrieved
        """
        return function
        
    
    @legacy_function
    def set_maximum_number_of_stars():
        """
        Update the maximum number of stars that can be
        handled by this instance. Need to set this number
        before calling :method:`initialize_code`. Cannot be
        changed once initialize_code has been called.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('maximum_number_of_stars', dtype='int32', direction=function.IN,
            description = "The new value of the maximum number of stars.")
        function.result_type = 'int32'
        function.result_doc = """
        0 - OK
            Current value was set
        -1 - ERROR
            The code cannot update the maximum number of stars
        """
        return function
    
    @legacy_function
    def set_ev_path():
        """
        Update the path to the EVtwin database.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('path', dtype='string', direction=function.IN)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def get_max_age_stop_condition():
        """
        Retrieve the current maximum age stop condition of this instance (in years).
        Evolution will stop once the star has reached this maximum age.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('max_age_stop_condition', dtype='float64', direction=function.OUT, unit=units.yr)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_max_age_stop_condition():
        """
        Set the new maximum age stop condition of this instance (in years).
        Evolution will stop once the star has reached this maximum age.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('max_age_stop_condition', dtype='float64', direction=function.IN, unit=units.yr)
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_min_timestep_stop_condition():
        """
        Retrieve the current minimum timestep stop condition of this instance (in seconds).
        Evolution will stop if the timestep required by the solver in order to converge
        has decreased below this minimum timestep.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('min_timestep', dtype='float64', direction=function.OUT, unit=units.s)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_min_timestep_stop_condition():
        """
        Set the new minimum timestep stop condition of this instance (in seconds).
        Evolution will stop if the timestep required by the solver in order to converge
        has decreased below this minimum timestep.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('min_timestep', dtype='float64', direction=function.IN, unit=units.s)
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_convective_overshoot_parameter():
        """
        Retrieve the current value of the convective overshoot parameter.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('convective_overshoot_parameter', dtype='float64', direction=function.OUT
            , description="The current value of the convective overshoot parameter.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_convective_overshoot_parameter():
        """
        Set the value of the convective overshoot parameter.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('convective_overshoot_parameter', dtype='float64', direction=function.IN
            , description="The new value of the convective overshoot parameter.")
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_mixing_length_ratio():
        """
        Retrieve the current value of the mixing length ratio.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('mixing_length_ratio', dtype='float64', direction=function.OUT
            , description="The current value of the mixing length ratio.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_mixing_length_ratio():
        """
        Set the value of the mixing length ratio.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('mixing_length_ratio', dtype='float64', direction=function.IN
            , description="The new value of the mixing length ratio.")
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_semi_convection_efficiency():
        """
        Retrieve the current value of the efficiency of semi-convection,
        after Langer, Sugimoto & Fricke 1983 (A&A).
        """
        function = LegacyFunctionSpecification()
        function.addParameter('semi_convection_efficiency', dtype='float64', direction=function.OUT
            , description="The current value of the efficiency of semi-convection.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_semi_convection_efficiency():
        """
        Set the value of the efficiency of semi-convection,
        after Langer, Sugimoto & Fricke 1983 (A&A).
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('semi_convection_efficiency', dtype='float64', direction=function.IN
            , description="The new value of the efficiency of semi-convection.")
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_thermohaline_efficiency():
        """
        Retrieve the current value of the thermohaline mixing parameter,
        probably only important for binaries and collision remnants.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('thermohaline_mixing_parameter', dtype='float64', direction=function.OUT
            , description="The current value of the thermohaline mixing parameter.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_thermohaline_efficiency():
        """
        Set the value of the thermohaline mixing parameter,
        probably only important for binaries and collision remnants.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('thermohaline_mixing_parameter', dtype='float64', direction=function.IN
            , description="The new value of the thermohaline mixing parameter.")
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_number_of_ionization_elements():
        """
        Retrieve the current number of elements used for ionization of this instance.
        With the default value (2), only the ionization of H and He are taken into account
        in the EoS. For values 3, 4, 5, 6, 7, 8, 9:
        the elements:          C, N, O, Ne,Mg,Si,Fe are also included. Don't try 9.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('number_of_ionization_elements', dtype='int32', direction=function.OUT
            , description="The current number of elements used for ionization in EoS solver of this instance.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_number_of_ionization_elements():
        """
        Set the new number of elements used for ionization of this instance.
        With the default value (2), only the ionization of H and He are taken into account
        in the EoS. For values 3, 4, 5, 6, 7, 8, 9:
        the elements:          C, N, O, Ne,Mg,Si,Fe are also included. Don't try 9.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('number_of_ionization_elements', dtype='int32', direction=function.IN
            , description="The new number of elements used for ionization in EoS solver of this instance.")
        function.result_type = 'int32'
        return function
    
    @legacy_function   
    def get_manual_mass_transfer_rate():
        """
        Retrieve the current user-specified mass transfer rate of the star. (negative for winds, positive for accretion)
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN)
        function.addParameter('mass_change', dtype='float64', unit=units.MSun/units.yr, direction=function.OUT)
        function.result_type = 'int32'
        return function
    
    @legacy_function   
    def set_manual_mass_transfer_rate():
        """
        Set a new user-specified mass transfer rate of the star. (negative for winds, positive for accretion)
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN)
        function.addParameter('mass_change', dtype='float64', unit=units.MSun/units.yr, direction=function.IN)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def get_wind_multiplier():
        """
        Stellar wind switch: can be modulated between 0.0 (no wind) and 1.0 (full strength)
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN)
        function.addParameter('wind_multiplier', dtype='float64', direction=function.OUT)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_wind_multiplier():
        """
        Stellar wind switch: can be modulated between 0.0 (no wind) and 1.0 (full strength)
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN)
        function.addParameter('wind_multiplier', dtype='float64', direction=function.IN)
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_AGB_wind_setting():
        """
        Retrieve the current AGB wind setting of this instance (1 or 2).
        (1) means use Wachter et al. (AGB) mass loss prescription.
        (2) means use Vasiliadis & Wood (AGB) mass loss rate.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('AGB_wind_setting', dtype='int32', direction=function.OUT
            , description="The current AGB wind setting of this instance.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_AGB_wind_setting():
        """
        Set the new AGB wind setting of this instance (1 or 2).
        (1) means use Wachter et al. (AGB) mass loss prescription.
        (2) means use Vasiliadis & Wood (AGB) mass loss rate.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('AGB_wind_setting', dtype='int32', direction=function.IN
            , description="The new AGB wind setting of this instance.")
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_RGB_wind_setting():
        """
        Retrieve the current RGB wind setting of this instance.
        (positive) means use Schroeder & Cuntz mass loss prescription.
        (negative) means use Reimers mass loss rate. (0) means none.
        The absolute value is used as efficiency factor.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('RGB_wind_setting', dtype='float64', direction=function.OUT
            , description="The current RGB wind setting of this instance.")
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_RGB_wind_setting():
        """
        Set the new RGB wind setting of this instance.
        (positive) means use Schroeder & Cuntz mass loss prescription.
        (negative) means use Reimers mass loss rate. (0) means none.
        The absolute value is used as efficiency factor.
        This needs to be set after calling :method:`initialize_code`. It will 
        be overridden by initialize_code otherwise.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('RGB_wind_setting', dtype='float64', direction=function.IN
            , description="The new RGB wind setting of this instance.")
        function.result_type = 'int32'
        return function
        
    @legacy_function
    def get_Ostar_wind_setting():
        """
        Retrieve the current wind setting for O/B stars, i.e. the efficiency 
        factor of the Vink et al. wind prescription.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('Ostar_wind_setting', dtype='float64', direction=function.OUT)
        function.result_type = 'int32'
        return function
    
    @legacy_function
    def set_Ostar_wind_setting():
        """
        Set the new wind setting for O/B stars, i.e. the efficiency 
        factor of the Vink et al. wind prescription.
        """
        function = LegacyFunctionSpecification()
        function.addParameter('Ostar_wind_setting', dtype='float64', direction=function.IN)
        function.result_type = 'int32'
        return function

    @legacy_function
    def get_verbosity():
        function = LegacyFunctionSpecification()
        function.addParameter('verbosity', dtype='int32', direction=function.OUT)
        function.result_type = 'int32'
        return function
    @legacy_function
    def set_verbosity():
        function = LegacyFunctionSpecification()
        function.addParameter('verbosity', dtype='int32', direction=function.IN)
        function.result_type = 'int32'
        return function

#~    @legacy_function
#~    def new_spinning_particle():
#~        """
#~        Define a new star in the code. The star will start with the given mass and given spin.
#~        """
#~        function = LegacyFunctionSpecification()
#~        function.can_handle_array = True
#~        function.addParameter('index_of_the_star', dtype='int32', direction=function.OUT
#~            , description="The new index for the star. This index can be used to refer to this star in other functions")
#~        function.addParameter('mass', dtype='float64', direction=function.IN
#~            , description="The initial mass of the star")
#~        function.addParameter('spin', dtype='float64', direction=function.IN
#~            , description="The initial spin of the star")
#~        function.result_type = 'int32'
#~        function.result_doc = """
#~        0 - OK
#~            New star was loaded and the index_of_the_star parameter set.
#~        -1 - ERROR
#~            New star could not be created.
#~        """
#~        return function
        
    @legacy_function
    def get_spin():
        """
        Retrieve the current spin period (in days) of this star.
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN
            , description="The index of the star to get the stellar type of")
        function.addParameter('spin', dtype='float64', direction=function.OUT
            , description="The current spin period (in days) of this star.")
        function.result_type = 'int32'
        return function
    
#~    @legacy_function   
#~    def get_mass_transfer_rate():
#~        """
#~        Retrieve the current mass transfer of the star to the other star.
#~        """
#~        function = LegacyFunctionSpecification()
#~        function.can_handle_array = True 
#~        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN
#~            , description="The index of the star to get the value of")
#~        function.addParameter('value', dtype='float64', direction=function.OUT
#~            , description="The mass transfer of the star to the other star.")
#~        function.result_type = 'int32'
#~        function.result_doc = """
#~        0 - OK
#~            The value has been retrieved.
#~        -1 - ERROR
#~            A star with the given index was not found.
#~        """
#~        return function
        
        
    
    @legacy_function   
    def get_wind_mass_loss_rate():
        """
        Retrieve the current mass loss rate of the star due to stellar wind.
        """
        function = LegacyFunctionSpecification()
        function.can_handle_array = True 
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN
            , description="The index of the star to get the value of")
        function.addParameter('value', dtype='float64', direction=function.OUT
            , description="The mass loss rate of the star due to stellar wind.")
        function.result_type = 'int32'
        return function
    
#~    @legacy_function   
#~    def new_stellar_model():
#~        """
#~        Define a new star model in the code. The star needs to be finalized 
#~        before it can evolve, see 'finalize_stellar_model'.
#~        """
#~        function = LegacyFunctionSpecification()
#~        function.must_handle_array = True
#~        for par in ['mass', 'radius', 'rho', 'pressure', 'X_H', 'X_He', 'X_C', 
#~                'X_N', 'X_O', 'X_Ne', 'X_Mg', 'X_Si', 'X_Fe']:
#~            function.addParameter(par, dtype='float64', direction=function.IN)
#~        function.addParameter('n', 'int32', function.LENGTH)
#~        function.result_type = 'int32'
#~        return function
#~    
#~    @legacy_function   
#~    def finalize_stellar_model():
#~        """
#~        Finalize the new star model defined by 'new_stellar_model'.
#~        """
#~        function = LegacyFunctionSpecification()
#~        function.addParameter('index_of_the_star', dtype='int32', 
#~            direction=function.OUT, description = "The new index for the star. "
#~            "This index can be used to refer to this star in other functions")
#~        function.addParameter('age_tag', dtype='float64', direction=function.IN, 
#~            description = "The initial age of the star")
#~        function.result_type = 'int32'
#~        return function
#~    
#~    @legacy_function
#~    def get_stellar_model_element():
#~        """
#~        Return properties of the stellar model at a specific zone.
#~        """
#~        function = LegacyFunctionSpecification()
#~        function.can_handle_array = True
#~        function.addParameter('index_of_the_zone', dtype='int32', direction=function.IN, 
#~            description="The index of the zone to get the values of")
#~        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN, 
#~            description="The index of the star to get the values of")
#~        for par in ['d_mass', 'mass', 'radius', 'density', 'pressure', 
#~                'entropy', 'temperature', 'luminosity', 'molecular_weight', 'X_H', 
#~                'X_He', 'X_C', 'X_N', 'X_O', 'X_Ne', 'X_Mg', 'X_Si', 'X_Fe']:
#~            function.addParameter(par, dtype='float64', direction=function.OUT)
#~        function.result_type = 'int32'
#~        return function
    
    @legacy_function   
    def write_star_to_file():
        function = LegacyFunctionSpecification()
        function.can_handle_array = True
        function.addParameter('index_of_the_star', dtype='int32', direction=function.IN)
        function.addParameter('filename', dtype='string', direction=function.IN)
        function.result_type = 'int32'
        return function
    


class EVtwin(StellarEvolution, InternalStellarStructure):
    
    def __init__(self, **options):
        InCodeComponentImplementation.__init__(self, EVtwinInterface(**options), **options)
        self.model_time = 0.0 | units.yr
    
    def define_parameters(self, object):
        object.add_boolean_parameter(
            "get_verbosity", 
            "set_verbosity",
            "verbosity", 
            "The level of terminal output, verbose or not.", 
            default_value = False
        )
        
        object.add_method_parameter(
            "get_maximum_number_of_stars",
            "set_maximum_number_of_stars",
            "maximum_number_of_stars", 
            "Maximum number of stars that can be allocated", 
            default_value = 10
        )
        
        object.add_method_parameter(
            "get_metallicity",
            "set_metallicity",
            "metallicity", 
            "Metallicity of all stats", 
            default_value = 0.02
        )
        
        object.add_method_parameter(
            None,
            "set_ev_path",
            "path_to_data", 
            "Path to the data directory", 
            default_value = self.data_directory
        )
        
        object.add_method_parameter(
            "get_max_age_stop_condition",
            "set_max_age_stop_condition",
            "max_age_stop_condition", 
            "The maximum age stop condition of this instance.",
            default_value = 1.0e12 | units.yr
        )
        
        object.add_method_parameter(
            "get_min_timestep_stop_condition",
            "set_min_timestep_stop_condition",
            "min_timestep_stop_condition", 
            "The minimum timestep stop condition of this instance.",
            default_value = 1.0e6 | units.s
        )
        
        object.add_method_parameter(
            "get_number_of_ionization_elements",
            "set_number_of_ionization_elements",
            "number_of_ionization_elements", 
            "The number of elements used for ionization in EoS solver of this instance.",
            default_value = 2
        )
        
        object.add_method_parameter(
            "get_convective_overshoot_parameter",
            "set_convective_overshoot_parameter",
            "convective_overshoot_parameter", 
            "The convective overshoot parameter.",
            default_value = 0.12
        )
        
        object.add_method_parameter(
            "get_mixing_length_ratio",
            "set_mixing_length_ratio",
            "mixing_length_ratio", 
            "The mixing-length ratio (alpha).",
            default_value = 2.0
        )
        
        object.add_method_parameter(
            "get_semi_convection_efficiency",
            "set_semi_convection_efficiency",
            "semi_convection_efficiency", 
            "The efficiency of semi-convection, after Langer, Sugimoto & Fricke 1983 (A&A).",
            default_value = 0.04
        )
        
        object.add_method_parameter(
            "get_thermohaline_efficiency",
            "set_thermohaline_efficiency",
            "thermohaline_efficiency", 
            "The thermohaline mixing parameter, probably only important for binaries and collision remnants.",
            default_value = 1.0
        )
        
        object.add_method_parameter(
            "get_AGB_wind_setting",
            "set_AGB_wind_setting",
            "AGB_wind_setting", 
            "The AGB wind setting: (1, 2) for (Wachter&al, Vasiliadis&Wood) mass loss.",
            default_value = 1
        )
        
        object.add_method_parameter(
            "get_RGB_wind_setting",
            "set_RGB_wind_setting",
            "RGB_wind_setting", 
            "The RGB wind setting: (positive, negative, 0) for (Schroeder&Cuntz, Reimers, none) mass loss.",
            default_value = 1.0
        )
        
        object.add_method_parameter(
            "get_Ostar_wind_setting",
            "set_Ostar_wind_setting",
            "OB_wind_setting", 
            "The wind setting for O/B stars, i.e. the efficiency factor of the Vink et al. wind prescription",
            default_value = 1.0
        )
    
    def define_particle_sets(self, object):
        object.define_set('particles', 'index_of_the_star')
        object.set_new('particles', 'new_particle_method')
        object.set_delete('particles', 'delete_star')
        
        object.add_getter('particles', 'get_radius', names = ('radius',))
        object.add_getter('particles', 'get_stellar_type', names = ('stellar_type',))
        object.add_getter('particles', 'get_mass', names = ('mass',))
        object.add_getter('particles', 'get_age', names = ('age',))
        object.add_getter('particles', 'get_time_step', names = ('time_step',))
        object.add_getter('particles', 'get_spin', names = ('spin',))
        object.add_getter('particles', 'get_luminosity', names = ('luminosity',))
        object.add_getter('particles', 'get_temperature', names = ('temperature',))
        object.add_method('particles', 'evolve_one_step')
        object.add_method('particles', 'evolve_for')
        InternalStellarStructure.define_particle_sets(self, object, set_name = 'particles')
        object.add_method('particles', 'get_stellar_model', 'internal_structure') 
        object.add_method('particles', 'write_star_to_file') 

        
#~        object.define_super_set('particles', ['native_stars', 'imported_stars'], 
#~            index_to_default_set = 0)
#~        
#~        object.define_set('imported_stars', 'index_of_the_star')
#~        object.set_new('imported_stars', 'finalize_stellar_model')
#~        object.set_delete('imported_stars', 'delete_star')
#~        
#~        object.define_set('native_stars', 'index_of_the_star')
#~        object.set_new('native_stars', 'new_particle')
#~        object.set_delete('native_stars', 'delete_star')
#~        
#~        for particle_set_name in ['native_stars', 'imported_stars']:
#~            object.add_getter(particle_set_name, 'get_radius', names = ('radius',))
#~            object.add_getter(particle_set_name, 'get_stellar_type', names = ('stellar_type',))
#~            object.add_getter(particle_set_name, 'get_mass', names = ('mass',))
#~            object.add_getter(particle_set_name, 'get_age', names = ('age',))
#~            object.add_getter(particle_set_name, 'get_time_step', names = ('time_step',))
#~            object.add_getter(particle_set_name, 'get_spin', names = ('spin',))
#~            object.add_getter(particle_set_name, 'get_luminosity', names = ('luminosity',))
#~            object.add_getter(particle_set_name, 'get_temperature', names = ('temperature',))
#~            object.add_method(particle_set_name, 'evolve_one_step')
#~            object.add_method(particle_set_name, 'evolve_for')
#~            InternalStellarStructure.define_particle_sets(self, object, set_name = particle_set_name)
#~            object.add_method(particle_set_name, 'get_stellar_model', 'internal_structure') 
#~            object.add_method(particle_set_name, 'write_star_to_file') 
    
    def define_state(self, object):
        StellarEvolution.define_state(self, object)
        object.add_method('EDIT', 'finalize_stellar_model')
        object.add_method('UPDATE', 'finalize_stellar_model')
        object.add_transition('RUN', 'UPDATE', 'finalize_stellar_model', False)
        object.add_method('EDIT', 'new_particle_method')
        object.add_method('UPDATE', 'new_particle_method')
        object.add_transition('RUN', 'UPDATE', 'new_particle_method', False)
    
    def define_errorcodes(self, object):
        InternalStellarStructure.define_errorcodes(self, object)
    
    def define_methods(self, object):
        InternalStellarStructure.define_methods(self, object)
        StellarEvolution.define_methods(self, object)
        object.add_method(
            "new_particle_method",
            (units.MSun, object.NO_UNIT, object.NO_UNIT),
            (object.INDEX, object.ERROR_CODE)
        )
        object.add_method(
            "get_mass_transfer_rate",
            (object.INDEX,),
            (units.MSun/units.yr, object.ERROR_CODE,)
        )
        object.add_method(
            "get_wind_mass_loss_rate",
            (object.INDEX,),
            (units.MSun/units.yr, object.ERROR_CODE,)
        )
        object.add_method(
            "get_spin", 
            (object.INDEX,), 
            (units.day, object.ERROR_CODE,)
        )
        object.add_method(
            "new_stellar_model", 
            (units.MSun, units.RSun, units.g / units.cm**3, units.barye, 
                object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, 
                object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.NO_UNIT,), 
            (object.ERROR_CODE,)
        )
        object.add_method(
            "finalize_stellar_model", 
            (units.yr,), 
            (object.INDEX, object.ERROR_CODE,)
        )
        object.add_method(
            "get_stellar_model_element", 
            (object.INDEX, object.INDEX,),
            (units.MSun, units.MSun, units.RSun, units.g / units.cm**3, units.barye, 
                object.NO_UNIT, units.K, units.LSun, units.amu,
                object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, 
                object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.NO_UNIT, object.ERROR_CODE)
        )
    
    def initialize_module_with_default_parameters(self):
        self.initialize_code()
        self.commit_parameters()
        
    def initialize_module_with_current_parameters(self):
        self.commit_parameters()
        
    def setup_particles(self, particles):
        self.particles.add_particles(particles)
        
    def commit_parameters(self):
        self.parameters.send_not_set_parameters_to_code()
        self.parameters.send_cached_parameters_to_code()
        self.overridden().commit_parameters()
                
    def get_stellar_model(self, index_of_the_star):
        if hasattr(index_of_the_star, '__iter__'):
            return [self._create_new_grid(self._specify_stellar_model, index_of_the_star = x) for x in index_of_the_star]
        else:
            return self._create_new_grid(self._specify_stellar_model, index_of_the_star = index_of_the_star)
    
    def get_range_in_zones(self, index_of_the_star):
        """
        Returns the inclusive range of defined zones/mesh-cells of the star.
        """
        return (1, self.get_number_of_zones(index_of_the_star))
    
    def _specify_stellar_model(self, definition, index_of_the_star = 0):
        definition.set_grid_range('get_range_in_zones')
        definition.add_getter('get_stellar_model_element', names=('d_mass', 'mass', 'radius', 
            'rho', 'pressure', 'entropy', 'temperature', 'luminosity', 'molecular_weight', 
            'X_H', 'X_He', 'X_C', 'X_N', 'X_O', 'X_Ne', 'X_Mg', 'X_Si', 'X_Fe'))
        definition.define_extra_keywords({'index_of_the_star':index_of_the_star})
    
    def new_particle_from_model(self, internal_structure, current_age, key=None):
        self.new_stellar_model(
            internal_structure.mass[::-1],
            internal_structure.radius[::-1],
            internal_structure.rho[::-1],
            internal_structure.pressure[::-1],
            internal_structure.X_H[::-1],
            internal_structure.X_He[::-1],
            internal_structure.X_C[::-1],
            internal_structure.X_N[::-1],
            internal_structure.X_O[::-1],
            internal_structure.X_Ne[::-1],
            internal_structure.X_Mg[::-1],
            internal_structure.X_Si[::-1],
            internal_structure.X_Fe[::-1]
        )
        tmp_star = datamodel.Particle(key=key)
        tmp_star.age_tag = current_age
        return self.imported_stars.add_particle(tmp_star)
    
    def new_particle_from_model2(self, internal_structure, current_age, key=None):
        if isinstance(internal_structure, dict):
            if "dmass" in internal_structure:
                mass_profile = internal_structure['dmass'][::-1]
            else:
                cumulative_mass_profile = [0.0] | units.MSun
                cumulative_mass_profile.extend(internal_structure['mass'])
                mass_profile = (cumulative_mass_profile[1:] - cumulative_mass_profile[:-1])[::-1]
            self.new_stellar_model(
                mass_profile,
                internal_structure['radius'][::-1],
                internal_structure['rho'][::-1],
                internal_structure['pressure'][::-1],
                internal_structure['X_H'][::-1],
                internal_structure['X_He'][::-1],
                internal_structure['X_C'][::-1],
                internal_structure['X_N'][::-1],
                internal_structure['X_O'][::-1],
                internal_structure['X_Ne'][::-1],
                internal_structure['X_Mg'][::-1],
                internal_structure['X_Si'][::-1],
                internal_structure['X_Fe'][::-1]
            )
        else:
            if hasattr(internal_structure, "dmass"):
                mass_profile = internal_structure.dmass[::-1]
            else:
                cumulative_mass_profile = [0.0] | units.MSun
                cumulative_mass_profile.extend(internal_structure.mass)
                mass_profile = (cumulative_mass_profile[1:] - cumulative_mass_profile[:-1])[::-1]
            self.new_stellar_model(
                mass_profile,
                internal_structure.radius[::-1],
                internal_structure.rho[::-1],
                internal_structure.pressure[::-1],
                internal_structure.X_H[::-1],
                internal_structure.X_He[::-1],
                internal_structure.X_C[::-1],
                internal_structure.X_N[::-1],
                internal_structure.X_O[::-1],
                internal_structure.X_Ne[::-1],
                internal_structure.X_Mg[::-1],
                internal_structure.X_Si[::-1],
                internal_structure.X_Fe[::-1]
            )
        tmp_star = datamodel.Particle(key=key)
        tmp_star.age_tag = current_age
        return self.imported_stars.add_particle(tmp_star)
